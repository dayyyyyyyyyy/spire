package com.project.spire.ui.create

import android.graphics.Bitmap
import android.graphics.Path
import android.graphics.PorterDuff
import android.graphics.PorterDuffXfermode
import android.util.Log
import android.view.MotionEvent
import androidx.lifecycle.LiveData
import androidx.lifecycle.MutableLiveData
import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.project.spire.utils.BitmapUtils
import com.project.spire.utils.PaintOptions
import kotlinx.coroutines.launch

class CanvasViewModel: ViewModel() {

    private var _masks = MutableLiveData<List<String>>()
    val masks: LiveData<List<String>>
        get() = _masks

    private var _labels = MutableLiveData<List<String>>()
    val labels: LiveData<List<String>>
        get() = _labels

    private var _originImageBitmap = MutableLiveData<Bitmap>()
    val originImageBitmap: LiveData<Bitmap>
        get() = _originImageBitmap

    fun setOriginImageBitmap(bitmap: Bitmap) {
        _originImageBitmap.value = bitmap
    }

    private var _backgroundMaskBitmap = MutableLiveData<Bitmap?>()
    val backgroundMaskBitmap: LiveData<Bitmap?>
        get() = _backgroundMaskBitmap

    /*
    fun setBackgroundMaskBitmap(bitmap: Bitmap, color: Int? = null) {
        _backgroundMaskBitmap.postValue(BitmapUtils.maskBlackToTransparent(bitmap, color))
    } */

    private val STROKE_PEN = 60f
    private val STROKE_ERASER = 80f
    private val MODE_CLEAR = PorterDuffXfermode(PorterDuff.Mode.CLEAR) // clears when overlapped

    private var _paths = LinkedHashMap<Path, PaintOptions>()
    val paths: LinkedHashMap<Path, PaintOptions>
        get() = _paths
    private var _paintOptions = PaintOptions(STROKE_PEN, null)
    val paintOptions: PaintOptions
        get() = _paintOptions

    private var _currentX = 0f
    private var _currentY = 0f
    private var _startX = 0f
    private var _startY = 0f

    private var _isEraseMode = MutableLiveData<Boolean>(false)
    val isEraseMode: LiveData<Boolean>
        get() = _isEraseMode
    private var _isPenMode = MutableLiveData<Boolean>(true)
    val isPenMode: LiveData<Boolean>
        get() = _isPenMode

    private var _isDrawing = MutableLiveData<Boolean>(false)
    val isDrawing: LiveData<Boolean>
        get() = _isDrawing

    private var _mPath: Path = Path()
    val mPath: Path
        get() = _mPath

    // mPath를 LiveData로 만들고 mPath를 observe하는 경우 화면 표시에 delay가 발생하여
    // 대신 isDrawing을 observe

    fun clearCanvas() {
        _mPath.reset()
        _paths = LinkedHashMap()
        _isEraseMode.postValue(false)
        _isPenMode.postValue(false)
        _isDrawing.postValue(true)
        _isDrawing.postValue(false)
    }

    fun changeEraseMode() {
        if (!_isEraseMode.value!!) {
            _isEraseMode.postValue(true)
            _isPenMode.postValue(false)
            _paintOptions.strokeWidth = STROKE_ERASER
            _paintOptions.xfermode = MODE_CLEAR
        }
        else {
            _isEraseMode.postValue(false)
        }
    }

    fun changePenMode() {
        if (!_isPenMode.value!!) {
            _isEraseMode.postValue(false)
            _isPenMode.postValue(true)
            _paintOptions.strokeWidth = STROKE_PEN
            _paintOptions.xfermode = null
        }
        else {
            _isPenMode.postValue(false)
        }
    }

    fun processCanvasMotionEvent(event: MotionEvent): Boolean {
        if (!_isPenMode.value!! and !_isEraseMode.value!!) return true;
        // don't need to track path is pen and eraser are both disabled

        val y = event.y
        val x = event.x
        if (event.pointerCount == 1) { // don't track on multi-touch
            when(event.action) {
                MotionEvent.ACTION_DOWN -> {
                    _startX = x
                    _startY = y

                    _mPath.reset()
                    _mPath.moveTo(x, y)
                    _currentX = x
                    _currentY = y

                    _isDrawing.postValue(true)
                    _isDrawing.postValue(false)
                }
                MotionEvent.ACTION_MOVE -> {
                    _mPath.quadTo(_currentX, _currentY, (x + _currentX) / 2, (y + _currentY) / 2)
                    _currentX = x
                    _currentY = y

                    _isDrawing.postValue(true)
                    _isDrawing.postValue(false)
                }
                MotionEvent.ACTION_UP -> {
                    _mPath.lineTo(_currentX, _currentY)

                    // draw a dot on click
                    if (_startX == _currentX && _startY == _currentY) {
                        _mPath.lineTo(_currentX, _currentY + 2)
                        _mPath.lineTo(_currentX + 1, _currentY + 2)
                        _mPath.lineTo(_currentX + 1, _currentY)
                    }
                    _paths[_mPath] = _paintOptions
                    _mPath = Path()
                    _paintOptions = PaintOptions(_paintOptions.strokeWidth, _paintOptions.xfermode)
                    _isDrawing.postValue(true)
                    _isDrawing.postValue(false)
                }
            }
        }
        return true
    }

    fun applyFetchedMask(mask: Bitmap) {
        _backgroundMaskBitmap.postValue(mask)
        Log.d("CanvasViewModel", "mask: ${mask.width} * ${mask.height}")
    }

    fun resetFetchedMask() {
        _backgroundMaskBitmap.postValue(null)
        // TODO: set onclick listener
    }

    fun fetch() {
        viewModelScope.launch {
            // TODO
        }
    }
}