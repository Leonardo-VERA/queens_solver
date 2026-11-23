package com.leonardo.queens

import android.Manifest
import android.app.Activity
import android.content.Intent
import android.content.pm.PackageManager
import android.graphics.Color
import android.graphics.Typeface
import android.media.projection.MediaProjectionConfig
import android.media.projection.MediaProjectionManager
import android.net.Uri
import android.os.Build
import android.os.Bundle
import android.provider.Settings
import android.view.Gravity
import android.widget.Button
import android.widget.LinearLayout
import android.widget.ScrollView
import android.widget.TextView
import android.widget.Toast

/**
 * Setup screen: grants the permissions, then starts the floating bubble.
 *
 * 1. "Afficher par-dessus d'autres applis" (system settings page)
 * 2. Notifications (Android 13+, for the "active" notification)
 * 3. Screen capture consent (asked by Android each time the bubble starts)
 */
class MainActivity : Activity() {

    private lateinit var status: TextView
    private lateinit var startButton: Button
    private lateinit var stopButton: Button

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        setContentView(buildLayout())
    }

    override fun onResume() {
        super.onResume()
        refresh()
    }

    private fun buildLayout(): ScrollView {
        val pad = dp(24)
        val column = LinearLayout(this).apply {
            orientation = LinearLayout.VERTICAL
            setPadding(pad, pad * 2, pad, pad)
        }
        column.addView(TextView(this).apply {
            text = "♛ Queens Solver"
            textSize = 28f
            typeface = Typeface.DEFAULT_BOLD
            setTextColor(Color.parseColor("#4B3BB5"))
        })
        column.addView(TextView(this).apply {
            text = "1. Touche « Activer la bulle ».\n" +
                "2. Accepte les autorisations (une fois), puis choisis « Écran entier » " +
                "quand Android demande quoi partager.\n" +
                "3. Ouvre Queens dans LinkedIn, grille entière visible.\n" +
                "4. Touche la bulle ♛ : des cercles montrent où poser les reines.\n" +
                "5. Touche à nouveau la bulle pour cacher les cercles.\n\n" +
                "Glisse la bulle pour la déplacer. Pour tout arrêter : « Arrêter » ici " +
                "ou dans la notification."
            textSize = 16f
            setPadding(0, pad, 0, pad)
        })
        status = TextView(this).apply { textSize = 15f; setPadding(0, 0, 0, pad) }
        column.addView(status)
        startButton = Button(this).apply {
            text = "Activer la bulle ♛"
            setOnClickListener { startFlow() }
        }
        stopButton = Button(this).apply {
            text = "Arrêter"
            setOnClickListener {
                startService(Intent(this@MainActivity, QueensService::class.java)
                    .setAction(QueensService.ACTION_STOP))
                status.postDelayed({ refresh() }, 300)
            }
        }
        column.addView(startButton)
        column.addView(stopButton)
        return ScrollView(this).apply { addView(column) }
    }

    private fun refresh() {
        val overlay = Settings.canDrawOverlays(this)
        status.text = when {
            QueensService.running -> "✅ Bulle active : va sur Queens et touche-la."
            !overlay -> "Autorisation requise : « Afficher par-dessus d'autres applis »."
            else -> "Prêt à activer la bulle."
        }
        stopButton.isEnabled = QueensService.running
        startButton.isEnabled = !QueensService.running
    }

    private fun startFlow() {
        if (!Settings.canDrawOverlays(this)) {
            Toast.makeText(this, "Active « Queens Solver » dans la liste, puis reviens.", Toast.LENGTH_LONG).show()
            startActivity(Intent(Settings.ACTION_MANAGE_OVERLAY_PERMISSION, Uri.parse("package:$packageName")))
            return
        }
        if (Build.VERSION.SDK_INT >= 33 &&
            checkSelfPermission(Manifest.permission.POST_NOTIFICATIONS) != PackageManager.PERMISSION_GRANTED
        ) {
            requestPermissions(arrayOf(Manifest.permission.POST_NOTIFICATIONS), REQ_NOTIFICATIONS)
            return  // continues in onRequestPermissionsResult
        }
        askScreenCapture()
    }

    override fun onRequestPermissionsResult(requestCode: Int, permissions: Array<out String>, grantResults: IntArray) {
        super.onRequestPermissionsResult(requestCode, permissions, grantResults)
        if (requestCode == REQ_NOTIFICATIONS) askScreenCapture()  // works without it too
    }

    private fun askScreenCapture() {
        val mpm = getSystemService(MediaProjectionManager::class.java)
        val intent = if (Build.VERSION.SDK_INT >= 34) {
            // Only "entire screen": a single-app capture would show our own app.
            mpm.createScreenCaptureIntent(MediaProjectionConfig.createConfigForDefaultDisplay())
        } else {
            mpm.createScreenCaptureIntent()
        }
        @Suppress("DEPRECATION")
        startActivityForResult(intent, REQ_CAPTURE)
    }

    @Deprecated("Plain Activity API, kept to avoid AndroidX dependencies")
    override fun onActivityResult(requestCode: Int, resultCode: Int, data: Intent?) {
        @Suppress("DEPRECATION")
        super.onActivityResult(requestCode, resultCode, data)
        if (requestCode != REQ_CAPTURE) return
        if (resultCode != RESULT_OK || data == null) {
            Toast.makeText(this, "Capture d'écran refusée.", Toast.LENGTH_SHORT).show()
            return
        }
        startForegroundService(
            Intent(this, QueensService::class.java)
                .putExtra(QueensService.EXTRA_RESULT_CODE, resultCode)
                .putExtra(QueensService.EXTRA_RESULT_DATA, data)
        )
        Toast.makeText(this, "Bulle ♛ activée : ouvre Queens !", Toast.LENGTH_SHORT).show()
        moveTaskToBack(true)
    }

    private fun dp(value: Int) = (value * resources.displayMetrics.density).toInt()

    companion object {
        private const val REQ_CAPTURE = 1
        private const val REQ_NOTIFICATIONS = 2
    }
}
