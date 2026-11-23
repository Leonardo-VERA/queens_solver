package com.leonardo.queens

import android.annotation.SuppressLint
import android.content.Context
import android.graphics.Canvas
import android.graphics.Color
import android.graphics.Paint
import android.graphics.RectF
import android.view.MotionEvent
import android.view.View
import android.view.ViewConfiguration
import android.view.WindowManager
import kotlin.math.abs
import kotlin.math.max

/** Queen markers drawn over the game. The window it lives in lets touches through. */
class MarkersView(context: Context) : View(context) {

    data class Result(
        val ok: Boolean,
        val message: String,
        val cell: Float,
        val queens: List<Pair<Float, Float>>,
    )

    private var result: Result? = null
    private val location = IntArray(2)
    private val density = resources.displayMetrics.density

    private val ring = Paint(Paint.ANTI_ALIAS_FLAG).apply {
        style = Paint.Style.STROKE
        color = Color.parseColor("#FF1F6B")
    }
    private val crown = Paint(Paint.ANTI_ALIAS_FLAG).apply {
        color = Color.parseColor("#FF1F6B")
        textAlign = Paint.Align.CENTER
    }
    private val labelText = Paint(Paint.ANTI_ALIAS_FLAG).apply {
        color = Color.WHITE
        textSize = 13 * density
        isFakeBoldText = true
    }
    private val labelBackground = Paint(Paint.ANTI_ALIAS_FLAG)
    private val labelRect = RectF()

    fun show(value: Result) {
        result = value
        invalidate()
    }

    fun clear() {
        result = null
        invalidate()
    }

    val isShowing get() = result != null

    override fun onDraw(canvas: Canvas) {
        val r = result ?: return
        // Positions come in screen pixels; this window may not start at (0, 0).
        getLocationOnScreen(location)
        canvas.save()
        canvas.translate(-location[0].toFloat(), -location[1].toFloat())

        var labelX = width / 2f - 150 * density
        var labelY = 120 * density
        if (r.ok && r.queens.isNotEmpty()) {
            ring.strokeWidth = max(3f, r.cell * 0.06f)
            crown.textSize = r.cell * 0.3f
            val radius = r.cell * 0.36f
            for ((x, y) in r.queens) {
                canvas.drawCircle(x, y, radius, ring)
                canvas.drawText("♛", x, y + crown.textSize * 0.35f, crown)
            }
            labelX = r.queens.minOf { it.first } - r.cell / 2
            val top = r.queens.minOf { it.second } - r.cell / 2
            labelY = if (top > 60 * density) top - 12 * density
            else r.queens.maxOf { it.second } + r.cell / 2 + 30 * density
        }

        val text = (if (r.ok) "♛ " else "✖ ") + r.message
        val pad = 8 * density
        val textWidth = labelText.measureText(text)
        labelBackground.color = Color.parseColor(if (r.ok) "#1F9D55" else "#C0392B")
        labelRect.set(labelX - pad, labelY - labelText.textSize - pad / 2, labelX + textWidth + pad, labelY + pad)
        canvas.drawRoundRect(labelRect, pad, pad, labelBackground)
        canvas.drawText(text, labelX, labelY, labelText)
        canvas.restore()
    }
}

/** Floating ♛ button: tap = solve / hide, drag = move. */
@SuppressLint("ViewConstructor")
class BubbleView(
    context: Context,
    private val windowManager: WindowManager,
    private val params: WindowManager.LayoutParams,
    private val onTap: () -> Unit,
) : View(context) {

    private val density = resources.displayMetrics.density
    private val slop = ViewConfiguration.get(context).scaledTouchSlop
    private val disc = Paint(Paint.ANTI_ALIAS_FLAG).apply { color = Color.parseColor("#7B61FF") }
    private val border = Paint(Paint.ANTI_ALIAS_FLAG).apply {
        style = Paint.Style.STROKE
        strokeWidth = 2 * density
        color = Color.WHITE
    }
    private val glyph = Paint(Paint.ANTI_ALIAS_FLAG).apply {
        color = Color.WHITE
        textAlign = Paint.Align.CENTER
        textSize = 24 * density
    }

    var busy = false
        set(value) {
            field = value
            invalidate()
        }

    private var downX = 0f
    private var downY = 0f
    private var startX = 0
    private var startY = 0
    private var dragging = false

    override fun onDraw(canvas: Canvas) {
        val cx = width / 2f
        val cy = height / 2f
        val radius = width / 2f - border.strokeWidth
        disc.alpha = if (busy) 120 else 230
        canvas.drawCircle(cx, cy, radius, disc)
        canvas.drawCircle(cx, cy, radius, border)
        canvas.drawText(if (busy) "…" else "♛", cx, cy + glyph.textSize * 0.35f, glyph)
    }

    @SuppressLint("ClickableViewAccessibility")
    override fun onTouchEvent(event: MotionEvent): Boolean {
        when (event.actionMasked) {
            MotionEvent.ACTION_DOWN -> {
                downX = event.rawX
                downY = event.rawY
                startX = params.x
                startY = params.y
                dragging = false
            }
            MotionEvent.ACTION_MOVE -> {
                val dx = event.rawX - downX
                val dy = event.rawY - downY
                if (!dragging && (abs(dx) > slop || abs(dy) > slop)) dragging = true
                if (dragging) {
                    params.x = startX + dx.toInt()
                    params.y = startY + dy.toInt()
                    windowManager.updateViewLayout(this, params)
                }
            }
            MotionEvent.ACTION_UP -> if (!dragging) {
                performClick()
                onTap()
            }
        }
        return true
    }

    override fun performClick(): Boolean {
        super.performClick()
        return true
    }
}
