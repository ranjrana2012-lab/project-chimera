/**
 * BSL Avatar Viewer - Three.js Scene Setup
 *
 * Initializes the 3D scene, camera, lighting, and renderer
 * for displaying the BSL signing avatar.
 */

class BSLAvatarViewer {
    constructor(canvasId, config = {}) {
        this.canvas = document.getElementById(canvasId);
        if (!this.canvas) {
            throw new Error(`Canvas element with id '${canvasId}' not found`);
        }

        // Configuration
        this.config = {
            camera: config.camera || {
                fov: 45,
                near: 0.1,
                far: 1000,
                position: { x: 0, y: 1.6, z: 3 },
                lookAt: { x: 0, y: 1.2, z: 0 }
            },
            renderer: config.renderer || {
                antialias: true,
                alpha: true,
                shadows: true
            },
            lights: config.lights || [
                { type: 'ambient', color: 0xffffff, intensity: 0.6 },
                { type: 'directional', color: 0xffffff, intensity: 0.8, position: { x: 5, y: 10, z: 7 } },
                { type: 'hemisphere', color: 0xffffff, groundColor: 0x444444, intensity: 0.4 }
            ],
            modelPath: config.modelPath || '/static/models/avatar.glb',
            ...config
        };

        // Scene components
        this.scene = null;
        this.camera = null;
        this.renderer = null;
        this.avatar = null;
        this.animationMixer = null;
        this.clock = new THREE.Clock();

        // State
        this.isLoaded = false;
        this.isPlaying = false;
        this.playbackSpeed = 1.0;
        this.currentExpression = 'neutral';

        // Event handlers
        this.onLoadCallbacks = [];
        this.onErrorCallbacks = [];
        this.onFrameCallbacks = [];

        // FPS tracking
        this.frameCount = 0;
        this.lastFpsUpdate = 0;
        this.fps = 0;

        this.init();
    }

    /**
     * Initialize the Three.js scene
     */
    init() {
        try {
            // Create scene
            this.scene = new THREE.Scene();
            this.scene.background = new THREE.Color(0xf0f0f0);

            // Create camera
            this.camera = new THREE.PerspectiveCamera(
                this.config.camera.fov,
                this.canvas.clientWidth / this.canvas.clientHeight,
                this.config.camera.near,
                this.config.camera.far
            );
            this.camera.position.set(
                this.config.camera.position.x,
                this.config.camera.position.y,
                this.config.camera.position.z
            );
            this.camera.lookAt(
                this.config.camera.lookAt.x,
                this.config.camera.lookAt.y,
                this.config.camera.lookAt.z
            );

            // Create renderer
            this.renderer = new THREE.WebGLRenderer({
                canvas: this.canvas,
                antialias: this.config.renderer.antialias,
                alpha: this.config.renderer.alpha
            });
            this.renderer.setSize(this.canvas.clientWidth, this.canvas.clientHeight);
            this.renderer.setPixelRatio(window.devicePixelRatio);
            this.renderer.shadowMap.enabled = this.config.renderer.shadows;
            this.renderer.shadowMap.type = THREE.PCFSoftShadowMap;
            this.renderer.outputEncoding = THREE.sRGBEncoding;
            this.renderer.toneMapping = THREE.ACESFilmicToneMapping;
            this.renderer.toneMappingExposure = 1.0;

            // Setup lights
            this.setupLights();

            // Setup ground plane
            this.setupGround();

            // Handle window resize
            window.addEventListener('resize', () => this.onWindowResize());

            // Start render loop
            this.animate();

            console.log('BSL Avatar Viewer initialized');
        } catch (error) {
            this.handleError(error);
        }
    }

    /**
     * Setup scene lighting
     */
    setupLights() {
        this.config.lights.forEach(lightConfig => {
            let light;

            switch (lightConfig.type) {
                case 'ambient':
                    light = new THREE.AmbientLight(lightConfig.color, lightConfig.intensity);
                    break;

                case 'directional':
                    light = new THREE.DirectionalLight(lightConfig.color, lightConfig.intensity);
                    light.position.set(
                        lightConfig.position.x,
                        lightConfig.position.y,
                        lightConfig.position.z
                    );
                    if (lightConfig.castShadow) {
                        light.castShadow = true;
                        light.shadow.mapSize.width = 2048;
                        light.shadow.mapSize.height = 2048;
                        light.shadow.camera.near = 0.5;
                        light.shadow.camera.far = 50;
                        light.shadow.camera.left = -5;
                        light.shadow.camera.right = 5;
                        light.shadow.camera.top = 5;
                        light.shadow.camera.bottom = -5;
                    }
                    break;

                case 'hemisphere':
                    light = new THREE.HemisphereLight(
                        lightConfig.color,
                        lightConfig.groundColor,
                        lightConfig.intensity
                    );
                    break;

                case 'point':
                    light = new THREE.PointLight(lightConfig.color, lightConfig.intensity);
                    if (lightConfig.position) {
                        light.position.set(
                            lightConfig.position.x,
                            lightConfig.position.y,
                            lightConfig.position.z
                        );
                    }
                    break;

                default:
                    console.warn(`Unknown light type: ${lightConfig.type}`);
                    return;
            }

            if (light) {
                this.scene.add(light);
            }
        });
    }

    /**
     * Setup ground plane
     */
    setupGround() {
        const groundGeometry = new THREE.PlaneGeometry(10, 10);
        const groundMaterial = new THREE.MeshStandardMaterial({
            color: 0xffffff,
            roughness: 0.8,
            metalness: 0.2
        });
        const ground = new THREE.Mesh(groundGeometry, groundMaterial);
        ground.rotation.x = -Math.PI / 2;
        ground.receiveShadow = true;
        this.scene.add(ground);
    }

    /**
     * Load avatar model from GLTF/GLB file
     */
    async loadAvatar(modelPath = null) {
        const path = modelPath || this.config.modelPath;

        try {
            const loader = new THREE.GLTFLoader();

            const gltf = await new Promise((resolve, reject) => {
                loader.load(
                    path,
                    resolve,
                    (progress) => {
                        const percent = (progress.loaded / progress.total * 100).toFixed(0);
                        console.log(`Loading avatar: ${percent}%`);
                    },
                    reject
                );
            });

            this.avatar = gltf.scene;

            // Enable shadows on avatar
            this.avatar.traverse((child) => {
                if (child.isMesh) {
                    child.castShadow = true;
                    child.receiveShadow = true;
                }
            });

            // Setup animation mixer
            if (gltf.animations && gltf.animations.length > 0) {
                this.animationMixer = new THREE.AnimationMixer(this.avatar);
                console.log(`Loaded ${gltf.animations.length} animations`);
            }

            // Add to scene
            this.scene.add(this.avatar);

            this.isLoaded = true;
            this.handleLoad();

            console.log('Avatar loaded successfully');
            return this.avatar;

        } catch (error) {
            this.handleError(error);
            throw error;
        }
    }

    /**
     * Set facial expression using morph targets
     */
    setExpression(expressionName, intensity = 1.0) {
        if (!this.avatar || !this.isLoaded) {
            console.warn('Avatar not loaded');
            return;
        }

        this.currentExpression = expressionName;

        // Expression morph target values
        const expressions = {
            neutral: { brows: 0, eyes_open: 0, smile: 0, mouth_open: 0 },
            happy: { brows: 0.2, eyes_open: -0.2, smile: 1, mouth_open: 0.1 },
            sad: { brows: -0.3, eyes_open: 0.3, smile: -0.5, mouth_open: 0 },
            surprised: { brows: 0.5, eyes_open: 0.5, smile: 0, mouth_open: 0.8 },
            angry: { brows: -0.4, eyes_open: 0.4, smile: -0.3, mouth_open: 0 },
            questioning: { brows: 0.3, eyes_open: 0.1, smile: 0.1, mouth_open: 0.2 },
            'brows-up': { brows: 0.5, eyes_open: 0, smile: 0, mouth_open: 0.1 },
            'brows-down': { brows: -0.4, eyes_open: 0.3, smile: 0, mouth_open: 0 }
        };

        const expression = expressions[expressionName] || expressions.neutral;

        // Apply to morph targets
        this.avatar.traverse((child) => {
            if (child.isMesh && child.morphTargetDictionary) {
                for (const [target, value] of Object.entries(expression)) {
                    const index = child.morphTargetDictionary[target];
                    if (index !== undefined) {
                        child.morphTargetInfluences[index] = value * intensity;
                    }
                }
            }
        });

        console.log(`Expression set to: ${expressionName}`);
    }

    /**
     * Set hand shape for BSL signing
     */
    setHandshape(hand, shape, intensity = 1.0) {
        if (!this.avatar || !this.isLoaded) {
            console.warn('Avatar not loaded');
            return;
        }

        // Hand shape morph target values
        const handshapes = {
            fist: [0, 0, 0, 0],
            open: [1, 1, 1, 1],
            point: [0, 1, 1, 1],
            peace: [0, 0, 1, 1]
        };

        const fingerValues = handshapes[shape] || handshapes.fist;

        // Apply to hand morph targets
        const handPrefix = hand === 'left' ? 'left_' : 'right_';
        this.avatar.traverse((child) => {
            if (child.isMesh && child.morphTargetDictionary) {
                for (let i = 0; i < 4; i++) {
                    const targetName = `${handPrefix}finger_${i}`;
                    const index = child.morphTargetDictionary[targetName];
                    if (index !== undefined) {
                        child.morphTargetInfluences[index] = fingerValues[i] * intensity;
                    }
                }
            }
        });

        console.log(`Handshape set to: ${hand} ${shape}`);
    }

    /**
     * Play animation clip
     */
    playAnimation(clipName) {
        if (!this.animationMixer) {
            console.warn('No animation mixer available');
            return;
        }

        // Find animation clip
        const clip = this.avatar.animations?.find(a => a.name === clipName);
        if (!clip) {
            console.warn(`Animation '${clipName}' not found`);
            return;
        }

        // Create and play action
        const action = this.animationMixer.clipAction(clip);
        action.reset();
        action.timeScale = this.playbackSpeed;
        action.setLoop(THREE.LoopOnce);
        action.clampWhenFinished = true;
        action.play();

        this.isPlaying = true;
        console.log(`Playing animation: ${clipName}`);
    }

    /**
     * Pause current animation
     */
    pauseAnimation() {
        if (this.animationMixer) {
            this.isPlaying = false;
            console.log('Animation paused');
        }
    }

    /**
     * Stop current animation
     */
    stopAnimation() {
        if (this.animationMixer) {
            this.animationMixer.stopAllAction();
            this.isPlaying = false;
            console.log('Animation stopped');
        }
    }

    /**
     * Set playback speed
     */
    setPlaybackSpeed(speed) {
        this.playbackSpeed = speed;

        if (this.animationMixer) {
            this.animationMixer.timeScale = speed;
        }

        console.log(`Playback speed: ${speed}x`);
    }

    /**
     * Render loop
     */
    animate() {
        requestAnimationFrame(() => this.animate());

        const delta = this.clock.getDelta();

        // Update animation mixer
        if (this.animationMixer && this.isPlaying) {
            this.animationMixer.update(delta * this.playbackSpeed);
        }

        // Update FPS counter
        this.updateFPS();

        // Render scene
        this.renderer.render(this.scene, this.camera);

        // Call frame callbacks
        this.onFrameCallbacks.forEach(callback => callback(delta));
    }

    /**
     * Update FPS display
     */
    updateFPS() {
        this.frameCount++;
        const now = performance.now();

        if (now - this.lastFpsUpdate >= 1000) {
            this.fps = Math.round(this.frameCount * 1000 / (now - this.lastFpsUpdate));
            this.frameCount = 0;
            this.lastFpsUpdate = now;
        }
    }

    /**
     * Handle window resize
     */
    onWindowResize() {
        if (!this.canvas || !this.camera || !this.renderer) return;

        const width = this.canvas.clientWidth;
        const height = this.canvas.clientHeight;

        this.camera.aspect = width / height;
        this.camera.updateProjectionMatrix();

        this.renderer.setSize(width, height);
    }

    /**
     * Handle successful load
     */
    handleLoad() {
        // Hide loading overlay
        const loadingOverlay = document.getElementById('loadingOverlay');
        if (loadingOverlay) {
            loadingOverlay.style.opacity = '0';
            setTimeout(() => {
                loadingOverlay.style.display = 'none';
            }, 500);
        }

        // Update status
        const statusIndicator = document.getElementById('statusIndicator');
        if (statusIndicator) {
            statusIndicator.classList.remove('loading');
            statusIndicator.classList.add('ready');
            statusIndicator.querySelector('.status-text').textContent = 'Ready';
        }

        // Enable controls
        const playBtn = document.getElementById('playBtn');
        const pauseBtn = document.getElementById('pauseBtn');
        const stopBtn = document.getElementById('stopBtn');
        if (playBtn) playBtn.disabled = false;
        if (pauseBtn) pauseBtn.disabled = false;
        if (stopBtn) stopBtn.disabled = false;

        // Call load callbacks
        this.onLoadCallbacks.forEach(callback => callback());
    }

    /**
     * Handle errors
     */
    handleError(error) {
        console.error('Avatar Viewer Error:', error);

        // Update status
        const statusIndicator = document.getElementById('statusIndicator');
        if (statusIndicator) {
            statusIndicator.classList.remove('loading');
            statusIndicator.classList.add('error');
            statusIndicator.querySelector('.status-text').textContent = 'Error';
        }

        // Call error callbacks
        this.onErrorCallbacks.forEach(callback => callback(error));
    }

    /**
     * Register callback for load event
     */
    onLoad(callback) {
        if (typeof callback === 'function') {
            this.onLoadCallbacks.push(callback);
        }
    }

    /**
     * Register callback for error event
     */
    onError(callback) {
        if (typeof callback === 'function') {
            this.onErrorCallbacks.push(callback);
        }
    }

    /**
     * Register callback for each frame
     */
    onFrame(callback) {
        if (typeof callback === 'function') {
            this.onFrameCallbacks.push(callback);
        }
    }

    /**
     * Get current FPS
     */
    getFPS() {
        return this.fps;
    }

    /**
     * Check if avatar is loaded
     */
    isAvatarLoaded() {
        return this.isLoaded;
    }

    /**
     * Dispose of resources
     */
    dispose() {
        if (this.renderer) {
            this.renderer.dispose();
        }

        if (this.avatar) {
            this.scene.remove(this.avatar);
            // Dispose geometries and materials
            this.avatar.traverse((child) => {
                if (child.isMesh) {
                    child.geometry.dispose();
                    if (child.material.map) child.material.map.dispose();
                    child.material.dispose();
                }
            });
        }
    }
}

// Export for use in other modules
if (typeof module !== 'undefined' && module.exports) {
    module.exports = BSLAvatarViewer;
}
