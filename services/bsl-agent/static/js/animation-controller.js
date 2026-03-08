/**
 * Animation Controller for BSL Avatar
 *
 * Manages animation playback, morph targets, and bone-based animations
 * using Three.js AnimationMixer and custom NMM animations.
 */

class AnimationController {
    constructor(viewer, nmmLoader) {
        this.viewer = viewer;
        this.nmmLoader = nmmLoader;

        // Playback state
        this.isPlaying = false;
        this.isPaused = false;
        this.currentTime = 0;
        this.duration = 0;
        this.playbackSpeed = 1.0;
        this.loop = false;

        // Current animation
        this.currentAnimation = null;
        this.currentAction = null;

        // Timeline callbacks
        this.onTimeUpdateCallbacks = [];
        this.onPlaybackStartCallbacks = [];
        this.onPlaybackEndCallbacks = [];
        this.onLoopCallbacks = [];

        // Bone references for manual manipulation
        this.bones = new Map();
        this.morphTargetMeshes = [];

        // Initialize
        this.init();
    }

    /**
     * Initialize animation controller
     */
    init() {
        // Find all bones in avatar
        if (this.viewer.avatar) {
            this.extractBones(this.viewer.avatar);
            this.extractMorphTargets(this.viewer.avatar);
        }

        // Register frame callback for animation updates
        this.viewer.onFrame((delta) => this.update(delta));
    }

    /**
     * Extract bone references from avatar
     */
    extractBones(object) {
        object.traverse((child) => {
            if (child.isBone) {
                this.bones.set(child.name, child);
            }
        });

        console.log(`Found ${this.bones.size} bones`);
    }

    /**
     * Extract morph target meshes
     */
    extractMorphTargets(object) {
        object.traverse((child) => {
            if (child.isMesh && child.morphTargetDictionary) {
                this.morphTargetMeshes.push(child);
            }
        });

        console.log(`Found ${this.morphTargetMeshes.length} meshes with morph targets`);
    }

    /**
     * Load and prepare NMM animation for playback
     */
    loadAnimation(animationData) {
        try {
            // Parse animation data
            const animation = this.nmmLoader.parseAnimation(animationData);
            this.currentAnimation = animation;
            this.duration = animation.duration;
            this.currentTime = 0;
            this.loop = animation.loop;

            console.log(`Animation loaded: ${animation.name} (${animation.duration}s)`);
            return animation;
        } catch (error) {
            console.error('Error loading animation:', error);
            throw error;
        }
    }

    /**
     * Play current animation
     */
    play() {
        if (!this.currentAnimation) {
            console.warn('No animation loaded');
            return;
        }

        this.isPlaying = true;
        this.isPaused = false;

        // Notify callbacks
        this.onPlaybackStartCallbacks.forEach(cb => cb());

        console.log('Animation playback started');
    }

    /**
     * Pause animation playback
     */
    pause() {
        if (!this.isPlaying) return;

        this.isPaused = true;
        console.log('Animation paused');
    }

    /**
     * Resume paused animation
     */
    resume() {
        if (!this.isPlaying || !this.isPaused) return;

        this.isPaused = false;
        console.log('Animation resumed');
    }

    /**
     * Stop animation playback
     */
    stop() {
        this.isPlaying = false;
        this.isPaused = false;
        this.currentTime = 0;

        // Reset to initial pose
        if (this.currentAnimation) {
            this.applyState(this.nmmLoader.interpolate(0));
        }

        this.onPlaybackEndCallbacks.forEach(cb => cb());
        console.log('Animation stopped');
    }

    /**
     * Seek to specific time
     */
    seek(time) {
        if (!this.currentAnimation) return;

        this.currentTime = Math.max(0, Math.min(time, this.duration));
        this.applyState(this.nmmLoader.interpolate(this.currentTime));
        this.notifyTimeUpdate();
    }

    /**
     * Set playback speed
     */
    setPlaybackSpeed(speed) {
        this.playbackSpeed = Math.max(0.1, Math.min(speed, 3.0));
        console.log(`Playback speed: ${this.playbackSpeed}x`);
    }

    /**
     * Set loop mode
     */
    setLoop(enabled) {
        this.loop = enabled;
        console.log(`Loop: ${enabled ? 'enabled' : 'disabled'}`);
    }

    /**
     * Update animation state (called each frame)
     */
    update(delta) {
        if (!this.isPlaying || this.isPaused || !this.currentAnimation) {
            return;
        }

        // Advance time
        this.currentTime += delta * this.playbackSpeed;

        // Handle loop or end
        if (this.currentTime >= this.duration) {
            if (this.loop) {
                this.currentTime = 0;
                this.onLoopCallbacks.forEach(cb => cb());
            } else {
                this.currentTime = this.duration;
                this.isPlaying = false;
                this.onPlaybackEndCallbacks.forEach(cb => cb());
            }
        }

        // Apply animation state
        const state = this.nmmLoader.interpolate(this.currentTime);
        if (state) {
            this.applyState(state);
        }

        // Notify time update
        this.notifyTimeUpdate();
    }

    /**
     * Apply animation state to avatar
     */
    applyState(state) {
        if (!state) return;

        // Apply morph targets
        this.applyMorphTargets(state.morphTargets);

        // Apply bone transforms
        this.applyBoneTransforms(state.bonePositions, state.boneRotations, state.boneScales);

        // Apply facial expression
        if (state.facialExpression) {
            this.viewer.setExpression(state.facialExpression);
        }

        // Apply handshape
        if (state.handshape) {
            this.viewer.setHandshape('right', state.handshape);
            this.viewer.setHandshape('left', state.handshape);
        }
    }

    /**
     * Apply morph target values
     */
    applyMorphTargets(morphTargets) {
        if (!morphTargets) return;

        for (const mesh of this.morphTargetMeshes) {
            if (!mesh.morphTargetDictionary) continue;

            for (const [targetName, value] of Object.entries(morphTargets)) {
                const index = mesh.morphTargetDictionary[targetName];
                if (index !== undefined) {
                    mesh.morphTargetInfluences[index] = value;
                }
            }
        }
    }

    /**
     * Apply bone transforms
     */
    applyBoneTransforms(positions, rotations, scales) {
        // Apply positions
        if (positions) {
            for (const [boneName, position] of Object.entries(positions)) {
                const bone = this.bones.get(boneName);
                if (bone) {
                    bone.position.set(position[0], position[1], position[2]);
                }
            }
        }

        // Apply rotations (quaternions)
        if (rotations) {
            for (const [boneName, rotation] of Object.entries(rotations)) {
                const bone = this.bones.get(boneName);
                if (bone) {
                    bone.quaternion.set(rotation[0], rotation[1], rotation[2], rotation[3]);
                }
            }
        }

        // Apply scales
        if (scales) {
            for (const [boneName, scale] of Object.entries(scales)) {
                const bone = this.bones.get(boneName);
                if (bone) {
                    bone.scale.set(scale[0], scale[1], scale[2]);
                }
            }
        }
    }

    /**
     * Set facial expression
     */
    setFacialExpression(expression, intensity = 1.0) {
        this.viewer.setExpression(expression, intensity);
    }

    /**
     * Set hand shape
     */
    setHandShape(hand, shape, intensity = 1.0) {
        this.viewer.setHandshape(hand, shape, intensity);
    }

    /**
     * Blend multiple facial expressions
     */
    blendExpressions(expressions) {
        // expressions: [{ name: 'happy', weight: 0.5 }, { name: 'surprised', weight: 0.5 }]

        // Get base expression values
        const expressionValues = {
            neutral: { brows: 0, eyes_open: 0, smile: 0, mouth_open: 0 },
            happy: { brows: 0.2, eyes_open: -0.2, smile: 1, mouth_open: 0.1 },
            sad: { brows: -0.3, eyes_open: 0.3, smile: -0.5, mouth_open: 0 },
            surprised: { brows: 0.5, eyes_open: 0.5, smile: 0, mouth_open: 0.8 },
            angry: { brows: -0.4, eyes_open: 0.4, smile: -0.3, mouth_open: 0 },
            questioning: { brows: 0.3, eyes_open: 0.1, smile: 0.1, mouth_open: 0.2 },
            'brows-up': { brows: 0.5, eyes_open: 0, smile: 0, mouth_open: 0.1 },
            'brows-down': { brows: -0.4, eyes_open: 0.3, smile: 0, mouth_open: 0 }
        };

        // Initialize blended values
        const blended = { brows: 0, eyes_open: 0, smile: 0, mouth_open: 0 };

        // Blend expressions
        for (const { name, weight } of expressions) {
            const values = expressionValues[name];
            if (values) {
                for (const key of Object.keys(blended)) {
                    blended[key] += values[key] * weight;
                }
            }
        }

        // Apply blended values
        this.applyMorphTargets(blended);
    }

    /**
     * Notify time update callbacks
     */
    notifyTimeUpdate() {
        this.onTimeUpdateCallbacks.forEach(cb => cb(this.currentTime, this.duration));
    }

    /**
     * Register callback for time updates
     */
    onTimeUpdate(callback) {
        if (typeof callback === 'function') {
            this.onTimeUpdateCallbacks.push(callback);
        }
    }

    /**
     * Register callback for playback start
     */
    onPlaybackStart(callback) {
        if (typeof callback === 'function') {
            this.onPlaybackStartCallbacks.push(callback);
        }
    }

    /**
     * Register callback for playback end
     */
    onPlaybackEnd(callback) {
        if (typeof callback === 'function') {
            this.onPlaybackEndCallbacks.push(callback);
        }
    }

    /**
     * Register callback for loop events
     */
    onLoop(callback) {
        if (typeof callback === 'function') {
            this.onLoopCallbacks.push(callback);
        }
    }

    /**
     * Get current playback state
     */
    getState() {
        return {
            isPlaying: this.isPlaying,
            isPaused: this.isPaused,
            currentTime: this.currentTime,
            duration: this.duration,
            playbackSpeed: this.playbackSpeed,
            loop: this.loop,
            progress: this.duration > 0 ? this.currentTime / this.duration : 0
        };
    }

    /**
     * Format time for display
     */
    formatTime(seconds) {
        const mins = Math.floor(seconds / 60);
        const secs = Math.floor(seconds % 60);
        return `${mins}:${secs.toString().padStart(2, '0')}`;
    }

    /**
     * Reset to initial state
     */
    reset() {
        this.stop();
        this.currentAnimation = null;
        this.duration = 0;
        this.currentTime = 0;
        this.onTimeUpdateCallbacks = [];
        this.onPlaybackStartCallbacks = [];
        this.onPlaybackEndCallbacks = [];
        this.onLoopCallbacks = [];
    }
}

// Export for use in other modules
if (typeof module !== 'undefined' && module.exports) {
    module.exports = AnimationController;
}
