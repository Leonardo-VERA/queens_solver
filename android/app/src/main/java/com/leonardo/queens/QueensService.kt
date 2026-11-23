package com.leonardo.queens

import android.app.Notification
import android.app.NotificationChannel
import android.app.NotificationManager
import android.app.PendingIntent
import android.app.Service
import android.content.Intent
import android.content.pm.ServiceInfo
import android.graphics.PixelFormat
import android.hardware.display.DisplayManager
import android.hardware.display.VirtualDisplay
import android.media.Image
import android.media.ImageReader
import android.media.projection.MediaProjection
import android.media.projection.MediaProjectionManager
import android.os.Build
import android.os.Handler
import android.os.HandlerThread
import android.os.IBinder
import android.os.Looper
import android.util.Log
import android.view.Gravity
import android.view.View
import android.view.WindowManager
import android.widget.Toast
import com.chaquo.python.Python
import com.chaquo.python.android.AndroidPlatform
import org.json.JSONObject
import java.util.concurrent.Executors

/**
 * Keeps the screen capture alive and shows the ♛ bubble over other apps.
 * Tap the bubble: hide overlays -> grab the latest frame -> Python solves it
 * (same code as the Streamlit app / Windows overlay) -> draw the markers.
 */
class QueensService : Service() {

    private lateinit var windowManager: WindowManager
    private val main = Handler(Looper.getMainLooper())
    private val worker = Executors.newSingleThreadExecutor()
    private val captureThread = HandlerThread("queens-capture").apply { start() }

    private var projection: MediaProjection? = null
    private var virtualDisplay: VirtualDisplay? = null
    private var reader: ImageReader? = null
    private val frameLock = Any()
    private var latestFrame: Image? = null

    private var bubble: BubbleView? = null
    private var markers: MarkersView? = null
    private var pythonReady = false
    private val hideMarkers = Runnable { markers?.clear() }

    override fun onBind(intent: Intent?): IBinder? = null

    override fun onStartCommand(intent: Intent?, flags: Int, startId: Int): Int {
        if (intent?.action == ACTION_STOP) {
            stopSelf()
            return START_NOT_STICKY
        }
        // Must be in the foreground (type mediaProjection) before getMediaProjection().
        startForeground(NOTIFICATION_ID, buildNotification(), ServiceInfo.FOREGROUND_SERVICE_TYPE_MEDIA_PROJECTION)
        if (projection == null && intent != null) {
            val code = intent.getIntExtra(EXTRA_RESULT_CODE, 0)
            val data: Intent? = if (Build.VERSION.SDK_INT >= 33) {
                intent.getParcelableExtra(EXTRA_RESULT_DATA, Intent::class.java)
            } else {
                @Suppress("DEPRECATION") intent.getParcelableExtra(EXTRA_RESULT_DATA)
            }
            if (data == null) {
                stopSelf()
                return START_NOT_STICKY
            }
            windowManager = getSystemService(WindowManager::class.java)
            if (!startCapture(code, data)) {
                toast("Capture d'écran indisponible : relance depuis l'app.")
                stopSelf()
                return START_NOT_STICKY
            }
            addOverlays()
            running = true
            worker.execute { startPython() }
        }
        return START_NOT_STICKY
    }

    // ── capture ─────────────────────────────────────────────────────────────
    private fun startCapture(code: Int, data: Intent): Boolean {
        val mpm = getSystemService(MediaProjectionManager::class.java)
        val proj = mpm.getMediaProjection(code, data) ?: return false
        projection = proj
        // Android stops the capture e.g. when the screen is locked: stop with it.
        proj.registerCallback(object : MediaProjection.Callback() {
            override fun onStop() {
                main.post { stopSelf() }
            }
        }, main)

        val bounds = windowManager.maximumWindowMetrics.bounds  // whole screen, real pixels
        val width = bounds.width()
        val height = bounds.height()
        val imageReader = ImageReader.newInstance(width, height, PixelFormat.RGBA_8888, 3)
        imageReader.setOnImageAvailableListener({ r ->
            val image = r.acquireLatestImage() ?: return@setOnImageAvailableListener
            synchronized(frameLock) {
                latestFrame?.close()
                latestFrame = image  // keep the newest frame, even if the screen stays still
            }
        }, Handler(captureThread.looper))
        reader = imageReader
        virtualDisplay = proj.createVirtualDisplay(
            "queens-capture", width, height, resources.displayMetrics.densityDpi,
            DisplayManager.VIRTUAL_DISPLAY_FLAG_AUTO_MIRROR, imageReader.surface, null, null,
        )
        return true
    }

    private class Frame(val bytes: ByteArray, val width: Int, val height: Int, val rowStride: Int)

    private fun copyLatestFrame(): Frame? = synchronized(frameLock) {
        val image = latestFrame ?: return null
        val plane = image.planes[0]
        val buffer = plane.buffer.duplicate().apply { rewind() }
        val bytes = ByteArray(plane.rowStride * image.height)
        buffer.get(bytes, 0, minOf(buffer.remaining(), bytes.size))
        Frame(bytes, image.width, image.height, plane.rowStride)
    }

    // ── python ──────────────────────────────────────────────────────────────
    private fun startPython() {
        try {
            if (!Python.isStarted()) Python.start(AndroidPlatform(this))
            Python.getInstance().getModule("android_bridge").callAttr("warm_up")
            pythonReady = true
        } catch (e: Throwable) {
            Log.e(TAG, "Python start failed", e)
            main.post { toast("Erreur au démarrage de Python : ${e.message}") }
        }
    }

    private fun solve(frame: Frame): MarkersView.Result {
        val json = Python.getInstance().getModule("android_bridge")
            .callAttr("solve_rgba", frame.bytes, frame.width, frame.height, frame.rowStride)
            .toString()
        val obj = JSONObject(json)
        val queens = obj.getJSONArray("queens").let { arr ->
            (0 until arr.length()).map { i ->
                val p = arr.getJSONArray(i)
                p.getDouble(0).toFloat() to p.getDouble(1).toFloat()
            }
        }
        return MarkersView.Result(obj.getBoolean("ok"), obj.getString("message"), obj.getDouble("cell").toFloat(), queens)
    }

    // ── bubble tap ──────────────────────────────────────────────────────────
    private fun onBubbleTap() {
        val bubbleView = bubble ?: return
        val markersView = markers ?: return
        if (bubbleView.busy) return
        if (markersView.isShowing) {  // second tap: hide the markers
            main.removeCallbacks(hideMarkers)
            markersView.clear()
            return
        }
        if (!pythonReady) {
            toast("Chargement de Python… réessaie dans quelques secondes.")
            return
        }
        bubbleView.busy = true
        bubbleView.visibility = View.INVISIBLE  // keep our own drawings out of the capture
        main.postDelayed({
            worker.execute {
                val result = try {
                    val frame = copyLatestFrame()
                    if (frame == null) MarkersView.Result(false, "Pas encore d'image de l'écran, réessaie.", 0f, emptyList())
                    else solve(frame)
                } catch (e: Throwable) {
                    Log.e(TAG, "Solve failed", e)
                    MarkersView.Result(false, "Erreur : ${e.message}", 0f, emptyList())
                }
                main.post {
                    bubbleView.visibility = View.VISIBLE
                    bubbleView.busy = false
                    markersView.show(result)
                    main.removeCallbacks(hideMarkers)
                    main.postDelayed(hideMarkers, if (result.ok) HIDE_AFTER_MS else 4000L)
                }
            }
        }, CAPTURE_DELAY_MS)
    }

    // ── overlay windows ─────────────────────────────────────────────────────
    private fun addOverlays() {
        val markersParams = WindowManager.LayoutParams(
            WindowManager.LayoutParams.MATCH_PARENT,
            WindowManager.LayoutParams.MATCH_PARENT,
            WindowManager.LayoutParams.TYPE_APPLICATION_OVERLAY,
            WindowManager.LayoutParams.FLAG_NOT_FOCUSABLE or
                WindowManager.LayoutParams.FLAG_NOT_TOUCHABLE or
                WindowManager.LayoutParams.FLAG_LAYOUT_IN_SCREEN or
                WindowManager.LayoutParams.FLAG_LAYOUT_NO_LIMITS,
            PixelFormat.TRANSLUCENT,
        ).apply {
            gravity = Gravity.TOP or Gravity.START
            // Android only lets touches pass through another app's window if
            // its opacity is <= 0.8. Semi-transparent markers are the goal anyway.
            alpha = MARKERS_OPACITY
            layoutInDisplayCutoutMode = WindowManager.LayoutParams.LAYOUT_IN_DISPLAY_CUTOUT_MODE_ALWAYS
            fitInsetsTypes = 0
        }
        markers = MarkersView(this).also { windowManager.addView(it, markersParams) }

        val size = (56 * resources.displayMetrics.density).toInt()
        val bubbleParams = WindowManager.LayoutParams(
            size, size,
            WindowManager.LayoutParams.TYPE_APPLICATION_OVERLAY,
            WindowManager.LayoutParams.FLAG_NOT_FOCUSABLE or WindowManager.LayoutParams.FLAG_LAYOUT_IN_SCREEN,
            PixelFormat.TRANSLUCENT,
        ).apply {
            gravity = Gravity.TOP or Gravity.START
            x = resources.displayMetrics.widthPixels - size - 16
            y = resources.displayMetrics.heightPixels / 3
            alpha = 0.85f
        }
        bubble = BubbleView(this, windowManager, bubbleParams) { onBubbleTap() }
            .also { windowManager.addView(it, bubbleParams) }
    }

    // ── notification ────────────────────────────────────────────────────────
    private fun buildNotification(): Notification {
        val nm = getSystemService(NotificationManager::class.java)
        nm.createNotificationChannel(
            NotificationChannel(CHANNEL_ID, "Bulle Queens", NotificationManager.IMPORTANCE_LOW)
        )
        val stop = PendingIntent.getService(
            this, 0, Intent(this, QueensService::class.java).setAction(ACTION_STOP),
            PendingIntent.FLAG_IMMUTABLE,
        )
        val open = PendingIntent.getActivity(
            this, 0, Intent(this, MainActivity::class.java), PendingIntent.FLAG_IMMUTABLE,
        )
        return Notification.Builder(this, CHANNEL_ID)
            .setSmallIcon(R.drawable.ic_crown)
            .setContentTitle("Queens Solver actif")
            .setContentText("Touche la bulle ♛ sur la grille Queens.")
            .setContentIntent(open)
            .setOngoing(true)
            .addAction(Notification.Action.Builder(null, "Arrêter", stop).build())
            .build()
    }

    private fun toast(text: String) = Toast.makeText(this, text, Toast.LENGTH_LONG).show()

    override fun onDestroy() {
        running = false
        main.removeCallbacksAndMessages(null)
        bubble?.let { runCatching { windowManager.removeView(it) } }
        markers?.let { runCatching { windowManager.removeView(it) } }
        virtualDisplay?.release()
        reader?.close()
        synchronized(frameLock) {
            latestFrame?.close()
            latestFrame = null
        }
        projection?.stop()
        captureThread.quitSafely()
        worker.shutdown()
        super.onDestroy()
    }

    companion object {
        const val ACTION_STOP = "com.leonardo.queens.STOP"
        const val EXTRA_RESULT_CODE = "result_code"
        const val EXTRA_RESULT_DATA = "result_data"
        private const val TAG = "QueensService"
        private const val CHANNEL_ID = "queens"
        private const val NOTIFICATION_ID = 1
        private const val CAPTURE_DELAY_MS = 250L
        private const val HIDE_AFTER_MS = 30_000L
        private const val MARKERS_OPACITY = 0.6f

        @Volatile
        var running = false
    }
}
