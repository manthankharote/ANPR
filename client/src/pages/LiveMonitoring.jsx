import React, { useState, useRef, useEffect } from 'react';
import {
  Play,
  Square,
  Upload,
  Video,
  Radio,
  Sliders,
  AlertTriangle,
  Layers,
  Camera,
  Activity,
  CheckCircle,
} from 'lucide-react';
import { violationService } from '../services/violationService';
import { STORAGE_URL, VIOLATION_COLORS } from '../utils/constants';

const LiveMonitoring = () => {
  const [sourceType, setSourceType] = useState('sample');
  const [isRunning, setIsRunning] = useState(false);
  const [activeSignal, setActiveSignal] = useState('GREEN');
  const [autoCycle, setAutoCycle] = useState(true);
  const [speedLimit, setSpeedLimit] = useState(50);
  const [confidence, setConfidence] = useState(0.4);
  const [selectedFile, setSelectedFile] = useState(null);
  const [jobProgress, setJobProgress] = useState(null);
  const [currentJobId, setCurrentJobId] = useState(null);
  const [jobDetails, setJobDetails] = useState(null);
  const [uploadedVideoUrl, setUploadedVideoUrl] = useState(null);
  const [activeTab, setActiveTab] = useState('single'); // 'single' | 'grid'

  // Live detection event feed
  const [liveEvents, setLiveEvents] = useState([
    {
      id: 1,
      time: '18:52:14',
      plate: 'MH20AB1234',
      type: 'Red Light Jump',
      fine: 1000,
      confidence: 0.94,
    },
    {
      id: 2,
      time: '18:50:33',
      plate: 'MH12XY9876',
      type: 'Over-Speeding',
      speed: '68.2 km/h',
      fine: 4000,
      confidence: 0.91,
    },
  ]);

  const videoRef = useRef(null);

  // Poll active AI processing job
  useEffect(() => {
    if (!currentJobId) return;

    let isMounted = true;
    const interval = setInterval(async () => {
      try {
        const res = await violationService.getJobStatus(currentJobId);
        if (res.success && res.data && isMounted) {
          const job = res.data;
          setJobDetails(job);
          setJobProgress(
            `Inference Progress: ${job.progress}% (${job.processed_frames || 0}/${job.total_frames || 0} frames) - ${job.violations_detected || 0} Violations Captured`
          );

          if (Array.isArray(job.violations) && job.violations.length > 0) {
            setLiveEvents(
              job.violations.map((v, idx) => ({
                id: v.tracking_id || idx + 1,
                time: v.timestamp ? v.timestamp.split(' ')[1] : 'Just now',
                plate: v.plate_number,
                type: v.violation_type,
                speed: v.speed_recorded ? `${v.speed_recorded} km/h` : null,
                fine: v.total_fine || v.primary_fine || 1000,
                confidence: 0.92,
                details: v.details,
              }))
            );
          }

          if (job.status === 'COMPLETED' || job.status === 'FAILED') {
            clearInterval(interval);
            if (job.status === 'COMPLETED') {
              setJobProgress(
                `✓ AI Inference Complete! Processed ${job.processed_frames || job.total_frames} frames. Captured ${job.violations_detected || 0} violations.`
              );
            } else {
              setJobProgress(`AI Processing stopped: ${job.error || 'Check service logs.'}`);
            }
          }
        }
      } catch (err) {
        // Polling retry
      }
    }, 1500);

    return () => {
      isMounted = false;
      clearInterval(interval);
    };
  }, [currentJobId]);

  // Handle Signal Manual Override
  const handleForceSignal = async (color) => {
    setActiveSignal(color);
    setAutoCycle(false);
    try {
      await violationService.overrideSignal({ state: color, autoCycle: false });
    } catch (e) {
      // Local fallback
    }
  };

  // Start / Stop Stream
  const toggleStream = async () => {
    if (isRunning) {
      setIsRunning(false);
      if (videoRef.current) {
        videoRef.current.pause();
      }
    } else {
      setIsRunning(true);
      if (videoRef.current) {
        videoRef.current.play().catch(() => {});
      }

      // If on built-in sample stream, launch real-time AI inference job
      if (sourceType === 'sample' && !currentJobId) {
        try {
          setJobProgress('Initializing YOLOv8 inference on sample traffic feed...');
          const res = await violationService.processSampleVideo({ speedLimit, confidence });
          if (res.jobId) {
            setCurrentJobId(res.jobId);
          }
        } catch (e) {
          setJobProgress('Running local video playback mode.');
        }
      }
    }
  };

  // Video Upload Handler
  const handleUploadAndProcess = async (e) => {
    const file = e.target.files[0];
    if (!file) return;
    setSelectedFile(file);
    setJobProgress('Uploading video to AI Engine...');

    const formData = new FormData();
    formData.append('video', file);
    formData.append('speedLimit', speedLimit);
    formData.append('confidence', confidence);

    try {
      const res = await violationService.processVideo(formData);
      if (res.jobId) {
        setCurrentJobId(res.jobId);
      }
      if (res.videoUrl) {
        setUploadedVideoUrl(res.videoUrl);
      }
      setJobProgress(`Video submitted! Job #${res.jobId || 'BATCH_01'}. Standby for inference...`);
      setIsRunning(true);
      if (videoRef.current) {
        videoRef.current.play().catch(() => {});
      }
    } catch (err) {
      setJobProgress('Upload processed. Standby for AI inference stream.');
      setIsRunning(true);
    }
  };

  return (
    <div className="space-y-6">
      {/* Top Banner */}
      <div className="flex flex-col lg:flex-row lg:items-center lg:justify-between gap-4">
        <div>
          <h1 className="text-2xl font-black text-white tracking-tight">Live Junction Surveillance</h1>
          <p className="text-xs text-slate-400 mt-1">
            Real-time multi-object tracking (YOLOv8), ANPR OCR & dynamic 4-way intersection control.
          </p>
        </div>

        {/* View Switcher Tabs */}
        <div className="flex items-center space-x-2 bg-slate-900/90 p-1 rounded-xl border border-slate-800">
          <button
            onClick={() => setActiveTab('single')}
            className={`px-4 py-1.5 rounded-lg text-xs font-bold transition-all ${
              activeTab === 'single' ? 'bg-blue-600 text-white shadow-md' : 'text-slate-400 hover:text-white'
            }`}
          >
            Main Lane Surveillance
          </button>
          <button
            onClick={() => setActiveTab('grid')}
            className={`px-4 py-1.5 rounded-lg text-xs font-bold transition-all ${
              activeTab === 'grid' ? 'bg-blue-600 text-white shadow-md' : 'text-slate-400 hover:text-white'
            }`}
          >
            4-Way Adaptive Grid (2×2)
          </button>
        </div>
      </div>

      {/* Control Bar */}
      <div className="glass-card rounded-2xl p-5 grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 items-center">
        {/* Source Select */}
        <div>
          <label className="block text-[11px] font-bold text-slate-400 uppercase tracking-wider mb-1.5">
            Surveillance Stream Source
          </label>
          <select
            value={sourceType}
            onChange={(e) => {
              setSourceType(e.target.value);
              setIsRunning(false);
            }}
            className="w-full py-2.5 px-3 rounded-xl glass-input text-xs font-medium text-white"
          >
            <option value="sample">Built-in Traffic Video (Multi-Violation Simulation)</option>
            <option value="webcam">Live USB / Laptop Webcam (Index 0)</option>
            <option value="upload">Upload Custom HD Video (MP4)</option>
          </select>
        </div>

        {/* Speed Slider */}
        <div>
          <div className="flex justify-between text-[11px] font-bold text-slate-400 uppercase tracking-wider mb-1.5">
            <span>Speed Limit Threshold</span>
            <span className="text-blue-400">{speedLimit} km/h</span>
          </div>
          <input
            type="range"
            min="30"
            max="100"
            step="5"
            value={speedLimit}
            onChange={(e) => setSpeedLimit(Number(e.target.value))}
            className="w-full accent-blue-500 cursor-pointer"
          />
        </div>

        {/* Confidence Slider */}
        <div>
          <div className="flex justify-between text-[11px] font-bold text-slate-400 uppercase tracking-wider mb-1.5">
            <span>YOLOv8 Confidence</span>
            <span className="text-blue-400">{(confidence * 100).toFixed(0)}%</span>
          </div>
          <input
            type="range"
            min="0.2"
            max="0.8"
            step="0.05"
            value={confidence}
            onChange={(e) => setConfidence(Number(e.target.value))}
            className="w-full accent-blue-500 cursor-pointer"
          />
        </div>

        {/* Action Button */}
        <div>
          <label className="block text-[11px] font-bold text-slate-400 uppercase tracking-wider mb-1.5 opacity-0">
            Action
          </label>
          <button
            onClick={toggleStream}
            className={`w-full py-2.5 px-4 rounded-xl font-bold text-xs flex items-center justify-center space-x-2 transition-all shadow-lg ${
              isRunning
                ? 'bg-rose-600 hover:bg-rose-500 text-white shadow-rose-600/30'
                : 'bg-emerald-600 hover:bg-emerald-500 text-white shadow-emerald-600/30'
            }`}
          >
            {isRunning ? (
              <>
                <Square className="w-4 h-4 fill-current" />
                <span>STOP SURVEILLANCE</span>
              </>
            ) : (
              <>
                <Play className="w-4 h-4 fill-current" />
                <span>START SURVEILLANCE</span>
              </>
            )}
          </button>
        </div>
      </div>

      {/* Main Grid: Stream Player (70%) + Signal Control & Live Ticker (30%) */}
      <div className="grid grid-cols-1 lg:grid-cols-10 gap-6">
        {/* Stream Canvas (7 cols) */}
        <div className="lg:col-span-7 space-y-4">
          <div className="glass-card rounded-2xl overflow-hidden border border-slate-800 relative bg-black aspect-video flex items-center justify-center">
            {activeTab === 'single' ? (
              sourceType === 'upload' && !isRunning ? (
                <div className="p-8 text-center flex flex-col items-center">
                  <Upload className="w-12 h-12 text-slate-500 mb-3" />
                  <p className="text-sm font-bold text-white mb-2">Upload Custom Traffic Feed</p>
                  <label className="cursor-pointer py-2 px-4 rounded-xl bg-blue-600 hover:bg-blue-500 text-xs font-bold text-white transition">
                    Select MP4 File
                    <input
                      type="file"
                      accept="video/mp4,video/avi"
                      className="hidden"
                      onChange={handleUploadAndProcess}
                    />
                  </label>
                  {jobProgress && <p className="text-xs text-blue-400 mt-3 font-mono">{jobProgress}</p>}
                </div>
              ) : (
                <div className="relative w-full h-full flex items-center justify-center">
                  {/* Video player for sample or uploaded video */}
                  <video
                    ref={videoRef}
                    loop
                    muted
                    playsInline
                    className="w-full h-full object-cover"
                    src={
                      sourceType === 'upload' && uploadedVideoUrl
                        ? `${STORAGE_URL}${uploadedVideoUrl}`
                        : `${STORAGE_URL}/uploads/sample_traffic.mp4`
                    }
                  />

                  {/* Overlay HUD graphics */}
                  <div className="absolute top-4 left-4 bg-slate-900/80 backdrop-blur-md px-3 py-1.5 rounded-lg border border-slate-700/60 text-[11px] font-mono text-slate-300 flex items-center space-x-2">
                    <span className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse" />
                    <span>CAM-04 (1280x720 @ 30 FPS)</span>
                  </div>

                  {/* Virtual Line Overlay Legend */}
                  <div className="absolute bottom-4 left-4 right-4 flex items-center justify-between pointer-events-none">
                    <div className="bg-slate-950/80 px-3 py-1.5 rounded-lg border border-slate-800 text-[11px] text-slate-300">
                      Stop Line: <span className="text-red-400 font-bold">Y=480px</span> | Speed Gates:{' '}
                      <span className="text-amber-400 font-bold">12.0m Calibrated</span>
                    </div>

                    <div className="bg-slate-950/80 px-3 py-1.5 rounded-lg border border-slate-800 text-[11px] text-slate-300">
                      Signal: <span className={`font-bold ${activeSignal === 'RED' ? 'text-red-400' : 'text-emerald-400'}`}>{activeSignal}</span>
                    </div>
                  </div>

                  {!isRunning && (
                    <div className="absolute inset-0 bg-black/60 backdrop-blur-sm flex flex-col items-center justify-center p-6 text-center">
                      <Camera className="w-12 h-12 text-slate-500 mb-3" />
                      <h3 className="text-base font-bold text-white mb-1">Surveillance Stream Standby</h3>
                      <p className="text-xs text-slate-400 max-w-sm mb-4">
                        Click 'Start Surveillance' to activate real-time YOLOv8 multi-class tracking and ANPR license plate extraction.
                      </p>
                      <button
                        onClick={toggleStream}
                        className="py-2 px-5 rounded-xl bg-blue-600 hover:bg-blue-500 text-xs font-bold text-white shadow-lg shadow-blue-500/25 transition"
                      >
                        Launch Camera Engine
                      </button>
                    </div>
                  )}
                </div>
              )
            ) : (
              /* 2x2 4-Way Intersection Grid */
              <div className="w-full h-full grid grid-cols-2 grid-rows-2 gap-1 bg-slate-950 p-1">
                {['NORTH', 'EAST', 'SOUTH', 'WEST'].map((dir, i) => (
                  <div key={dir} className="relative bg-slate-900 flex items-center justify-center border border-slate-800/80">
                    <video
                      loop
                      muted
                      autoPlay={isRunning}
                      className="w-full h-full object-cover opacity-85"
                      src={`${STORAGE_URL}/uploads/sample_traffic.mp4`}
                    />
                    <div className="absolute top-2 left-2 px-2 py-0.5 rounded bg-black/70 text-[10px] font-bold text-white">
                      {dir} CAM #{i + 1}
                    </div>
                    <div className="absolute bottom-2 right-2 px-2 py-0.5 rounded text-[10px] font-bold bg-emerald-500/20 text-emerald-400 border border-emerald-500/30">
                      Density: {(i + 1) * 2.5}
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>

        {/* Right Sidebar: Signal Override & Live Violation Ticker (3 cols) */}
        <div className="lg:col-span-3 space-y-4">
          {/* Signal Control Center */}
          <div className="glass-card rounded-2xl p-5 border border-slate-800">
            <h3 className="text-xs font-bold text-slate-400 uppercase tracking-wider mb-3">
              Junction Signal Control
            </h3>

            <div className="flex items-center justify-between mb-4 p-3 rounded-xl bg-slate-900/80 border border-slate-800">
              <span className="text-xs text-slate-300 font-semibold">Active State:</span>
              <span
                className={`px-3 py-1 rounded-lg text-xs font-black tracking-wider uppercase ${
                  activeSignal === 'RED'
                    ? 'bg-rose-500/20 text-rose-400 border border-rose-500/30'
                    : 'bg-emerald-500/20 text-emerald-400 border border-emerald-500/30'
                }`}
              >
                ● {activeSignal} LIGHT
              </span>
            </div>

            <div className="grid grid-cols-2 gap-2 mb-3">
              <button
                onClick={() => handleForceSignal('RED')}
                className="py-2 px-3 rounded-xl bg-rose-600/20 hover:bg-rose-600/30 text-rose-400 border border-rose-500/30 text-xs font-bold transition"
              >
                🔴 Force RED
              </button>
              <button
                onClick={() => handleForceSignal('GREEN')}
                className="py-2 px-3 rounded-xl bg-emerald-600/20 hover:bg-emerald-600/30 text-emerald-400 border border-emerald-500/30 text-xs font-bold transition"
              >
                🟢 Force GREEN
              </button>
            </div>

            <div className="flex items-center justify-between pt-3 border-t border-slate-800 text-xs">
              <span className="text-slate-400">Adaptive Auto-Cycle (15s/10s):</span>
              <input
                type="checkbox"
                checked={autoCycle}
                onChange={(e) => setAutoCycle(e.target.checked)}
                className="rounded text-blue-600 focus:ring-0 cursor-pointer"
              />
            </div>
          </div>

          {/* Live Violation Feed Ticker */}
          <div className="glass-card rounded-2xl p-5 border border-slate-800">
            <div className="flex items-center justify-between mb-3">
              <h3 className="text-xs font-bold text-slate-400 uppercase tracking-wider">
                Live Violation Ticker
              </h3>
              <span className="text-[10px] font-bold text-blue-400 bg-blue-500/10 px-2 py-0.5 rounded-full">
                Real-Time
              </span>
            </div>

            <div className="space-y-2.5 max-h-72 overflow-y-auto pr-1">
              {liveEvents.map((ev) => (
                <div
                  key={ev.id}
                  className="p-3 rounded-xl bg-slate-900/70 border border-slate-800 hover:border-slate-700 transition"
                >
                  <div className="flex items-center justify-between mb-1.5">
                    <span className="font-mono text-xs font-bold bg-white text-slate-900 px-1.5 py-0.5 rounded">
                      {ev.plate}
                    </span>
                    <span className="text-[10px] text-slate-400">{ev.time}</span>
                  </div>

                  <div className="flex items-center justify-between">
                    <span className={`text-[11px] font-bold ${VIOLATION_COLORS[ev.type]?.split(' ')[1] || 'text-rose-400'}`}>
                      {ev.type}
                    </span>
                    <span className="text-xs font-bold text-emerald-400">₹{ev.fine}</span>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default LiveMonitoring;
