/**
 * BSL Avatar Viewer - Enhanced Edition
 *
 * Extended avatar viewer with:
 * - Playback controls (play, pause, stop, speed, scrub)
 * - Recording (video/gif capture)
 * - Full-screen mode
 * - Preset animation buttons
 * - Timeline editor for sequencing
 * - Camera controls
 */

class BSLAvatarEnhanced extends BSLAvatarViewer {
    constructor(canvasId, config = {}) {
        super(canvasId, config);

        // Enhanced state
        this.isRecording = false;
        this.recordingStartTime = 0;
        this.recordingFrames = [];
        this.recordingMediaRecorder = null;
        this.recordingChunks = [];
        this.isFullScreen = false;
        this.currentTime = 0;
        this.totalDuration = 0;
        this.timelineMarkers = [];
        this.selectedMarker = null;

        // Camera control state
        this.cameraControls = null;
        this.enableCameraControls = config.enableCameraControls !== false;

        // Initialize enhanced features
        this.initEnhancedFeatures();
    }

    /**
     * Initialize enhanced features
     */
    initEnhancedFeatures() {
        // Setup camera controls if enabled
        if (this.enableCameraControls) {
            this.initCameraControls();
        }

        // Setup recording canvas
        this.setupRecordingCanvas();

        // Load timeline markers from localStorage
        this.loadTimelineMarkers();

        console.log('Enhanced features initialized');
    }

    /**
     * Initialize orbit camera controls
     */
    initCameraControls() {
        // Simple orbit controls implementation
        let isDragging = false;
        let previousMousePosition = { x: 0, y: 0 };
        let spherical = { radius: 3, phi: Math.PI / 4, theta: 0 };

        const updateCameraPosition = () => {
            this.camera.position.x = spherical.radius * Math.sin(spherical.phi) * Math.sin(spherical.theta);
            this.camera.position.y = spherical.radius * Math.cos(spherical.phi);
            this.camera.position.z = spherical.radius * Math.sin(spherical.phi) * Math.cos(spherical.theta);
            this.camera.lookAt(0, 1.2, 0);
        };

        this.canvas.addEventListener('mousedown', (e) => {
            isDragging = true;
            previousMousePosition = { x: e.clientX, y: e.clientY };
        });

        this.canvas.addEventListener('mousemove', (e) => {
            if (!isDragging) return;

            const deltaX = e.clientX - previousMousePosition.x;
            const deltaY = e.clientY - previousMousePosition.y;

            spherical.theta += deltaX * 0.01;
            spherical.phi = Math.max(0.1, Math.min(Math.PI - 0.1, spherical.phi + deltaY * 0.01));

            updateCameraPosition();
            previousMousePosition = { x: e.clientX, y: e.clientY };
        });

        this.canvas.addEventListener('mouseup', () => {
            isDragging = false;
        });

        this.canvas.addEventListener('wheel', (e) => {
            e.preventDefault();
            spherical.radius = Math.max(1.5, Math.min(10, spherical.radius + e.deltaY * 0.01));
            updateCameraPosition();
        });

        this.cameraControls = {
            spherical,
            updateCameraPosition
        };
    }

    /**
     * Setup recording canvas
     */
    setupRecordingCanvas() {
        this.recordingCanvas = document.createElement('canvas');
        this.recordingCanvas.width = this.canvas.width;
        this.recordingCanvas.height = this.canvas.height;
        this.recordingContext = this.recordingCanvas.getContext('2d');
    }

    // ========================================================================
    // PLAYBACK CONTROLS
    // ========================================================================

    /**
     * Play animation from specific time
     */
    playFromTime(time) {
        this.currentTime = Math.max(0, Math.min(time, this.totalDuration));

        if (this.animationMixer && this.animationMixer.clipAction) {
            const action = this.animationMixer.clipAction(this.currentClip);
            action.time = this.currentTime;
            action.play();
        }

        this.isPlaying = true;
        this.notifyPlaybackChange('play', { time: this.currentTime });
    }

    /**
     * Seek to specific time
     */
    seek(time) {
        const wasPlaying = this.isPlaying;

        if (wasPlaying) {
            this.pauseAnimation();
        }

        this.currentTime = Math.max(0, Math.min(time, this.totalDuration));

        if (this.animationMixer) {
            this.animationMixer.update(this.currentTime - (this.animationMixer.time || 0));
        }

        if (wasPlaying) {
            this.playAnimation();
        }

        this.notifyPlaybackChange('seek', { time: this.currentTime });
    }

    /**
     * Step forward one frame
     */
    stepForward() {
        const frameTime = 1 / 30; // Assuming 30 FPS
        this.seek(this.currentTime + frameTime);
    }

    /**
     * Step backward one frame
     */
    stepBackward() {
        const frameTime = 1 / 30;
        this.seek(this.currentTime - frameTime);
    }

    /**
     * Set playback speed
     */
    setPlaybackSpeed(speed) {
        super.setPlaybackSpeed(speed);
        this.notifyPlaybackChange('speed', { speed });
    }

    /**
     * Get current playback time
     */
    getCurrentTime() {
        return this.currentTime;
    }

    /**
     * Get total animation duration
     */
    getTotalDuration() {
        return this.totalDuration;
    }

    /**
     * Notify listeners of playback changes
     */
    notifyPlaybackChange(event, data) {
        const customEvent = new CustomEvent(`avatar:${event}`, {
            detail: { ...data, viewer: this }
        });
        this.canvas.dispatchEvent(customEvent);
    }

    // ========================================================================
    // RECORDING CONTROLS
    // ========================================================================

    /**
     * Start recording video
     */
    async startRecording(format = 'webm') {
        if (this.isRecording) {
            console.warn('Already recording');
            return;
        }

        try {
            const stream = this.canvas.captureStream(30); // 30 FPS
            this.recordingMediaRecorder = new MediaRecorder(stream, {
                mimeType: `video/${format}`,
                videoBitsPerSecond: 5000000 // 5 Mbps
            });

            this.recordingChunks = [];
            this.recordingMediaRecorder.ondataavailable = (e) => {
                if (e.data.size > 0) {
                    this.recordingChunks.push(e.data);
                }
            };

            this.recordingMediaRecorder.onstop = () => {
                this.saveRecording(format);
            };

            this.recordingMediaRecorder.start();
            this.isRecording = true;
            this.recordingStartTime = Date.now();

            console.log('Recording started');
            this.notifyRecordingChange('started');

        } catch (error) {
            console.error('Error starting recording:', error);
            this.notifyRecordingChange('error', { error });
        }
    }

    /**
     * Stop recording
     */
    stopRecording() {
        if (!this.isRecording) {
            console.warn('Not recording');
            return;
        }

        if (this.recordingMediaRecorder && this.recordingMediaRecorder.state !== 'inactive') {
            this.recordingMediaRecorder.stop();
        }

        this.isRecording = false;
        console.log('Recording stopped');
        this.notifyRecordingChange('stopped');
    }

    /**
     * Save recording to file
     */
    saveRecording(format) {
        const blob = new Blob(this.recordingChunks, { type: `video/${format}` });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `bsl-avatar-${Date.now()}.${format}`;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        URL.revokeObjectURL(url);

        this.notifyRecordingChange('saved', { url, format });
    }

    /**
     * Capture current frame as image
     */
    captureFrame(format = 'png') {
        this.recordingContext.drawImage(this.canvas, 0, 0);

        const dataUrl = this.recordingCanvas.toDataURL(`image/${format}`);
        const a = document.createElement('a');
        a.href = dataUrl;
        a.download = `bsl-avatar-frame-${Date.now()}.${format}`;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);

        this.notifyRecordingChange('frame-captured', { format });
    }

    /**
     * Check if currently recording
     */
    isRecordingActive() {
        return this.isRecording;
    }

    /**
     * Get recording duration
     */
    getRecordingDuration() {
        if (!this.isRecording) return 0;
        return (Date.now() - this.recordingStartTime) / 1000;
    }

    /**
     * Notify listeners of recording changes
     */
    notifyRecordingChange(event, data) {
        const customEvent = new CustomEvent(`avatar:recording:${event}`, {
            detail: { ...data, viewer: this }
        });
        this.canvas.dispatchEvent(customEvent);
    }

    // ========================================================================
    // FULL-SCREEN MODE
    // ========================================================================

    /**
     * Toggle full-screen mode
     */
    toggleFullScreen() {
        if (this.isFullScreen) {
            this.exitFullScreen();
        } else {
            this.enterFullScreen();
        }
    }

    /**
     * Enter full-screen mode
     */
    enterFullScreen() {
        const element = this.canvas.parentElement || this.canvas;

        if (element.requestFullscreen) {
            element.requestFullscreen();
        } else if (element.webkitRequestFullscreen) {
            element.webkitRequestFullscreen();
        } else if (element.mozRequestFullScreen) {
            element.mozRequestFullScreen();
        } else if (element.msRequestFullscreen) {
            element.msRequestFullscreen();
        }

        this.isFullScreen = true;
        this.canvas.classList.add('fullscreen');
        this.notifyFullScreenChange('entered');
    }

    /**
     * Exit full-screen mode
     */
    exitFullScreen() {
        if (document.exitFullscreen) {
            document.exitFullscreen();
        } else if (document.webkitExitFullscreen) {
            document.webkitExitFullscreen();
        } else if (document.mozCancelFullScreen) {
            document.mozCancelFullScreen();
        } else if (document.msExitFullscreen) {
            document.msExitFullscreen();
        }

        this.isFullScreen = false;
        this.canvas.classList.remove('fullscreen');
        this.notifyFullScreenChange('exited');
    }

    /**
     * Check if in full-screen mode
     */
    isInFullScreen() {
        return this.isFullScreen || document.fullscreenElement !== null;
    }

    /**
     * Notify listeners of full-screen changes
     */
    notifyFullScreenChange(event) {
        const customEvent = new CustomEvent(`avatar:fullscreen:${event}`, {
            detail: { viewer: this }
        });
        this.canvas.dispatchEvent(customEvent);
    }

    // ========================================================================
    // PRESET ANIMATIONS
    // ========================================================================

    /**
     * Play preset animation
     */
    playPreset(presetName) {
        const presets = {
            'greeting': ['phrase_hello', 'expression_happy'],
            'goodbye': ['phrase_goodbye', 'expression_neutral'],
            'thank-you': ['phrase_thank_you', 'expression_happy'],
            'yes': ['phrase_yes', 'expression_happy'],
            'no': ['phrase_no', 'expression_neutral'],
            'alphabet-a': ['letter_A'],
            'count-1': ['number_1'],
            'happy': ['emotion_happy'],
            'sad': ['emotion_sad'],
            'surprised': ['emotion_surprised']
        };

        const preset = presets[presetName];
        if (!preset) {
            console.warn(`Unknown preset: ${presetName}`);
            return;
        }

        // Play animation sequence
        preset.forEach((item, index) => {
            setTimeout(() => {
                if (item.startsWith('phrase_') || item.startsWith('letter_') || item.startsWith('number_')) {
                    this.playAnimation(item);
                } else if (item.startsWith('expression_') || item.startsWith('emotion_')) {
                    const expression = item.replace('expression_', '').replace('emotion_', '');
                    this.setExpression(expression);
                }
            }, index * 1000);
        });

        console.log(`Playing preset: ${presetName}`);
        this.notifyPresetPlayed(presetName);
    }

    /**
     * Get available presets
     */
    getAvailablePresets() {
        return {
            greetings: ['greeting', 'goodbye', 'thank-you'],
            responses: ['yes', 'no'],
            learning: ['alphabet-a', 'count-1'],
            emotions: ['happy', 'sad', 'surprised']
        };
    }

    /**
     * Notify listeners of preset playback
     */
    notifyPresetPlayed(presetName) {
        const customEvent = new CustomEvent('avatar:preset-played', {
            detail: { preset: presetName, viewer: this }
        });
        this.canvas.dispatchEvent(customEvent);
    }

    // ========================================================================
    // TIMELINE EDITOR
    // ========================================================================

    /**
     * Add timeline marker
     */
    addTimelineMarker(time, label, color = '#4CAF50') {
        const marker = {
            id: `marker-${Date.now()}`,
            time,
            label,
            color,
            createdAt: new Date().toISOString()
        };

        this.timelineMarkers.push(marker);
        this.saveTimelineMarkers();
        this.sortTimelineMarkers();

        this.notifyTimelineChange('marker-added', marker);
        return marker;
    }

    /**
     * Remove timeline marker
     */
    removeTimelineMarker(markerId) {
        const index = this.timelineMarkers.findIndex(m => m.id === markerId);
        if (index !== -1) {
            const marker = this.timelineMarkers.splice(index, 1)[0];
            this.saveTimelineMarkers();
            this.notifyTimelineChange('marker-removed', marker);
            return true;
        }
        return false;
    }

    /**
     * Update timeline marker
     */
    updateTimelineMarker(markerId, updates) {
        const marker = this.timelineMarkers.find(m => m.id === markerId);
        if (marker) {
            Object.assign(marker, updates);
            this.saveTimelineMarkers();
            this.sortTimelineMarkers();
            this.notifyTimelineChange('marker-updated', marker);
            return true;
        }
        return false;
    }

    /**
     * Get timeline markers
     */
    getTimelineMarkers() {
        return [...this.timelineMarkers];
    }

    /**
     * Get nearest marker to time
     */
    getNearestMarker(time) {
        if (this.timelineMarkers.length === 0) return null;

        return this.timelineMarkers.reduce((nearest, marker) => {
            const markerDistance = Math.abs(marker.time - time);
            const nearestDistance = Math.abs(nearest.time - time);
            return markerDistance < nearestDistance ? marker : nearest;
        });
    }

    /**
     * Jump to marker
     */
    jumpToMarker(markerId) {
        const marker = this.timelineMarkers.find(m => m.id === markerId);
        if (marker) {
            this.seek(marker.time);
            this.selectedMarker = markerId;
            this.notifyTimelineChange('marker-selected', marker);
            return true;
        }
        return false;
    }

    /**
     * Sort timeline markers by time
     */
    sortTimelineMarkers() {
        this.timelineMarkers.sort((a, b) => a.time - b.time);
    }

    /**
     * Save timeline markers to localStorage
     */
    saveTimelineMarkers() {
        try {
            localStorage.setItem('bsl-avatar-timeline-markers', JSON.stringify(this.timelineMarkers));
        } catch (e) {
            console.warn('Could not save timeline markers:', e);
        }
    }

    /**
     * Load timeline markers from localStorage
     */
    loadTimelineMarkers() {
        try {
            const stored = localStorage.getItem('bsl-avatar-timeline-markers');
            if (stored) {
                this.timelineMarkers = JSON.parse(stored);
                this.sortTimelineMarkers();
            }
        } catch (e) {
            console.warn('Could not load timeline markers:', e);
        }
    }

    /**
     * Clear all timeline markers
     */
    clearTimelineMarkers() {
        this.timelineMarkers = [];
        this.saveTimelineMarkers();
        this.notifyTimelineChange('markers-cleared');
    }

    /**
     * Notify listeners of timeline changes
     */
    notifyTimelineChange(event, data = {}) {
        const customEvent = new CustomEvent(`avatar:timeline:${event}`, {
            detail: { ...data, viewer: this }
        });
        this.canvas.dispatchEvent(customEvent);
    }

    // ========================================================================
    // RENDER LOOP OVERRIDE
    // ========================================================================

    animate() {
        super.animate();

        // Update current time based on playback
        if (this.isPlaying && this.animationMixer) {
            this.currentTime = this.animationMixer.time || this.currentTime;
        }

        // Capture frame if recording
        if (this.isRecording) {
            this.recordingContext.drawImage(this.canvas, 0, 0);
        }
    }

    // ========================================================================
    // DISPOSE OVERRIDE
    // ========================================================================

    dispose() {
        // Stop recording if active
        if (this.isRecording) {
            this.stopRecording();
        }

        // Exit full-screen if active
        if (this.isInFullScreen()) {
            this.exitFullScreen();
        }

        // Call parent dispose
        super.dispose();

        console.log('Enhanced avatar viewer disposed');
    }
}

// Export for use in other modules
if (typeof module !== 'undefined' && module.exports) {
    module.exports = BSLAvatarEnhanced;
}
