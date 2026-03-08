/**
 * NMM (Neural Model Format) Animation Loader
 *
 * Parses and loads NMM format animations for BSL signing.
 * Supports keyframes, morph targets, bone transforms, and timeline-based playback.
 */

class NMMLoader {
    constructor() {
        this.animations = new Map();
        this.currentAnimation = null;
    }

    /**
     * Parse NMM animation from JSON data
     */
    parseAnimation(jsonData) {
        try {
            const data = typeof jsonData === 'string' ? JSON.parse(jsonData) : jsonData;

            // Validate format
            if (!data.name || !data.duration) {
                throw new Error('Invalid NMM format: missing required fields');
            }

            const animation = {
                name: data.name,
                duration: data.duration,
                fps: data.fps || 30,
                loop: data.loop || false,
                easing: data.easing || 'linear',
                keyframes: [],
                metadata: data.metadata || {}
            };

            // Parse keyframes
            if (data.keyframes && Array.isArray(data.keyframes)) {
                animation.keyframes = data.keyframes.map(kf => ({
                    time: kf.time,
                    morphTargets: kf.morph_targets || {},
                    boneRotations: kf.bone_rotations || {},
                    bonePositions: kf.bone_positions || {},
                    boneScales: kf.bone_scales || {},
                    facialExpression: kf.facial_expression || null,
                    handshape: kf.handshape || null,
                    lipSyncValue: kf.lip_sync_value || 0
                }));
            }

            // Sort keyframes by time
            animation.keyframes.sort((a, b) => a.time - b.time);

            // Store animation
            this.animations.set(animation.name, animation);

            console.log(`NMM animation loaded: ${animation.name} (${animation.keyframes.length} keyframes)`);
            return animation;

        } catch (error) {
            console.error('Error parsing NMM animation:', error);
            throw error;
        }
    }

    /**
     * Load NMM animation from URL
     */
    async loadFromUrl(url) {
        try {
            const response = await fetch(url);
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            const jsonData = await response.json();
            return this.parseAnimation(jsonData);
        } catch (error) {
            console.error(`Error loading NMM animation from ${url}:`, error);
            throw error;
        }
    }

    /**
     * Get animation by name
     */
    getAnimation(name) {
        return this.animations.get(name);
    }

    /**
     * Set current animation
     */
    setCurrentAnimation(name) {
        const animation = this.animations.get(name);
        if (!animation) {
            throw new Error(`Animation '${name}' not found`);
        }
        this.currentAnimation = animation;
        return animation;
    }

    /**
     * Get current animation
     */
    getCurrentAnimation() {
        return this.currentAnimation;
    }

    /**
     * Interpolate animation state at given time
     */
    interpolate(time, animationName = null) {
        const animation = animationName ?
            this.animations.get(animationName) :
            this.currentAnimation;

        if (!animation || animation.keyframes.length === 0) {
            return null;
        }

        // Handle looping
        let effectiveTime = time;
        if (animation.loop) {
            effectiveTime = time % animation.duration;
        } else {
            effectiveTime = Math.min(time, animation.duration);
        }

        // Clamp to valid range
        effectiveTime = Math.max(0, effectiveTime);

        // Find surrounding keyframes
        let prevKf = null;
        let nextKf = null;

        for (const kf of animation.keyframes) {
            if (kf.time <= effectiveTime) {
                prevKf = kf;
            }
            if (kf.time >= effectiveTime && !nextKf) {
                nextKf = kf;
                break;
            }
        }

        // Handle edge cases
        if (!prevKf && !nextKf) return null;
        if (!prevKf) return this.keyframeToState(nextKf);
        if (!nextKf) return this.keyframeToState(prevKf);
        if (prevKf === nextKf) return this.keyframeToState(prevKf);

        // Calculate interpolation factor
        const timeRange = nextKf.time - prevKf.time;
        const t = timeRange > 0 ? (effectiveTime - prevKf.time) / timeRange : 0;

        // Apply easing function
        const easedT = this.applyEasing(t, animation.easing);

        // Interpolate state
        return this.interpolateKeyframes(prevKf, nextKf, easedT);
    }

    /**
     * Apply easing function to interpolation factor
     */
    applyEasing(t, easing) {
        switch (easing) {
            case 'easeIn':
                return t * t;
            case 'easeOut':
                return 1 - (1 - t) * (1 - t);
            case 'easeInOut':
                return t < 0.5 ? 2 * t * t : 1 - 2 * (1 - t) * (1 - t);
            case 'easeInCubic':
                return t * t * t;
            case 'easeOutCubic':
                return 1 - (1 - t) * (1 - t) * (1 - t);
            case 'easeInOutCubic':
                return t < 0.5 ? 4 * t * t * t : 1 - 4 * (1 - t) * (1 - t) * (1 - t);
            case 'linear':
            default:
                return t;
        }
    }

    /**
     * Interpolate between two keyframes
     */
    interpolateKeyframes(kf1, kf2, t) {
        const state = {
            time: kf1.time + t * (kf2.time - kf1.time),
            morphTargets: {},
            boneRotations: {},
            bonePositions: {},
            boneScales: {},
            facialExpression: kf2.facialExpression || kf1.facialExpression,
            handshape: kf2.handshape || kf1.handshape,
            lipSyncValue: this.lerp(kf1.lipSyncValue, kf2.lipSyncValue, t)
        };

        // Interpolate morph targets
        const allMorphKeys = new Set([
            ...Object.keys(kf1.morphTargets),
            ...Object.keys(kf2.morphTargets)
        ]);
        for (const key of allMorphKeys) {
            const v1 = kf1.morphTargets[key] || 0;
            const v2 = kf2.morphTargets[key] || 0;
            state.morphTargets[key] = this.lerp(v1, v2, t);
        }

        // Interpolate bone rotations (quaternion slerp approximation)
        const allRotKeys = new Set([
            ...Object.keys(kf1.boneRotations),
            ...Object.keys(kf2.boneRotations)
        ]);
        for (const key of allRotKeys) {
            const q1 = kf1.boneRotations[key] || [0, 0, 0, 1];
            const q2 = kf2.boneRotations[key] || [0, 0, 0, 1];
            state.boneRotations[key] = this.slerp(q1, q2, t);
        }

        // Interpolate bone positions
        const allPosKeys = new Set([
            ...Object.keys(kf1.bonePositions),
            ...Object.keys(kf2.bonePositions)
        ]);
        for (const key of allPosKeys) {
            const p1 = kf1.bonePositions[key] || [0, 0, 0];
            const p2 = kf2.bonePositions[key] || [0, 0, 0];
            state.bonePositions[key] = [
                this.lerp(p1[0], p2[0], t),
                this.lerp(p1[1], p2[1], t),
                this.lerp(p1[2], p2[2], t)
            ];
        }

        // Interpolate bone scales
        const allScaleKeys = new Set([
            ...Object.keys(kf1.boneScales),
            ...Object.keys(kf2.boneScales)
        ]);
        for (const key of allScaleKeys) {
            const s1 = kf1.boneScales[key] || [1, 1, 1];
            const s2 = kf2.boneScales[key] || [1, 1, 1];
            state.boneScales[key] = [
                this.lerp(s1[0], s2[0], t),
                this.lerp(s1[1], s2[1], t),
                this.lerp(s1[2], s2[2], t)
            ];
        }

        return state;
    }

    /**
     * Linear interpolation
     */
    lerp(a, b, t) {
        return a + t * (b - a);
    }

    /**
     * Quaternion spherical linear interpolation (simplified)
     */
    slerp(q1, q2, t) {
        // Convert to arrays if needed
        const qa = Array.isArray(q1) ? q1 : [q1.x, q1.y, q1.z, q1.w];
        const qb = Array.isArray(q2) ? q2 : [q2.x, q2.y, q2.z, q2.w];

        // Calculate dot product
        let dot = 0;
        for (let i = 0; i < 4; i++) {
            dot += qa[i] * qb[i];
        }

        // If quaternions are too close, use linear interpolation
        if (Math.abs(dot) > 0.9995) {
            const result = [];
            for (let i = 0; i < 4; i++) {
                result.push(this.lerp(qa[i], qb[i], t));
            }
            // Normalize
            const len = Math.sqrt(result[0]**2 + result[1]**2 + result[2]**2 + result[3]**2);
            return result.map(v => v / len);
        }

        // Ensure shortest path
        if (dot < 0) {
            for (let i = 0; i < 4; i++) {
                qb[i] = -qb[i];
            }
            dot = -dot;
        }

        // Calculate interpolation factors
        const theta = Math.acos(Math.min(Math.max(dot, -1), 1));
        const sinTheta = Math.sin(theta);
        const factorA = Math.sin((1 - t) * theta) / sinTheta;
        const factorB = Math.sin(t * theta) / sinTheta;

        // Interpolate
        const result = [];
        for (let i = 0; i < 4; i++) {
            result.push(factorA * qa[i] + factorB * qb[i]);
        }

        return result;
    }

    /**
     * Convert keyframe to state object
     */
    keyframeToState(keyframe) {
        return {
            time: keyframe.time,
            morphTargets: { ...keyframe.morphTargets },
            boneRotations: { ...keyframe.boneRotations },
            bonePositions: { ...keyframe.bonePositions },
            boneScales: { ...keyframe.boneScales },
            facialExpression: keyframe.facialExpression,
            handshape: keyframe.handshape,
            lipSyncValue: keyframe.lipSyncValue
        };
    }

    /**
     * Generate sample NMM animation for testing
     */
    generateSampleAnimation(name = 'sample', duration = 2) {
        const keyframes = [];

        // Starting pose
        keyframes.push({
            time: 0,
            morphTargets: {
                brows: 0,
                eyes_open: 0,
                smile: 0,
                mouth_open: 0
            },
            bonePositions: {
                right_hand: [0.2, 1.0, 0],
                left_hand: [-0.2, 1.0, 0]
            },
            facialExpression: 'neutral',
            lipSyncValue: 0
        });

        // Mid pose
        keyframes.push({
            time: duration * 0.5,
            morphTargets: {
                brows: 0.3,
                eyes_open: 0.1,
                smile: 0.5,
                mouth_open: 0.2
            },
            bonePositions: {
                right_hand: [0.4, 1.3, 0.3],
                left_hand: [-0.4, 1.3, 0.3]
            },
            facialExpression: 'happy',
            lipSyncValue: 0.5
        });

        // End pose
        keyframes.push({
            time: duration,
            morphTargets: {
                brows: 0,
                eyes_open: 0,
                smile: 0,
                mouth_open: 0
            },
            bonePositions: {
                right_hand: [0.2, 1.0, 0],
                left_hand: [-0.2, 1.0, 0]
            },
            facialExpression: 'neutral',
            lipSyncValue: 0
        });

        return this.parseAnimation({
            name,
            duration,
            fps: 30,
            loop: false,
            easing: 'easeInOut',
            keyframes,
            metadata: {
                generated: true,
                description: 'Sample animation for testing'
            }
        });
    }

    /**
     * Clear all loaded animations
     */
    clear() {
        this.animations.clear();
        this.currentAnimation = null;
    }

    /**
     * Get list of loaded animation names
     */
    getAnimationNames() {
        return Array.from(this.animations.keys());
    }
}

// Export for use in other modules
if (typeof module !== 'undefined' && module.exports) {
    module.exports = NMMLoader;
}
