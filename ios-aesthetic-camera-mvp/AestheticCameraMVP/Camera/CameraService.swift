import AVFoundation
import UIKit

enum CameraError: LocalizedError {
    case denied
    case setupFailed
    case captureFailed

    var errorDescription: String? {
        switch self {
        case .denied: return "Camera access is denied."
        case .setupFailed: return "Camera setup failed."
        case .captureFailed: return "Photo capture failed."
        }
    }
}

final class CameraService: NSObject, ObservableObject {
    let session = AVCaptureSession()
    @Published private(set) var isReady = false
    @Published private(set) var position: AVCaptureDevice.Position = .back
    @Published private(set) var zoom: CGFloat = 1
    @Published private(set) var zoomOptions: [CGFloat] = [1, 2, 3]
    @Published var flashMode: AVCaptureDevice.FlashMode = .off

    private let queue = DispatchQueue(label: "aesthetic.camera.queue")
    private let output = AVCapturePhotoOutput()
    private var input: AVCaptureDeviceInput?
    private var activeDevice: AVCaptureDevice?
    private var processor: PhotoProcessor?

    func requestPermission() async -> Bool {
        switch AVCaptureDevice.authorizationStatus(for: .video) {
        case .authorized: return true
        case .notDetermined: return await AVCaptureDevice.requestAccess(for: .video)
        default: return false
        }
    }

    func start() {
        queue.async { [weak self] in
            guard let self else { return }
            if self.input == nil { self.configure(position: self.position, zoom: self.zoom) }
            if !self.session.isRunning { self.session.startRunning() }
        }
    }

    func stop() {
        queue.async { [weak self] in
            if self?.session.isRunning == true { self?.session.stopRunning() }
        }
    }

    func switchCamera() {
        queue.async { [weak self] in
            guard let self else { return }
            self.configure(position: self.position == .back ? .front : .back, zoom: 1)
        }
    }

    func setZoom(_ value: CGFloat) {
        queue.async { [weak self] in
            guard let self else { return }
            if value < 1, self.position == .back {
                self.configure(position: .back, zoom: value)
                return
            }
            guard let device = self.activeDevice else { return }
            do {
                try device.lockForConfiguration()
                device.videoZoomFactor = min(max(value, device.minAvailableVideoZoomFactor), min(device.maxAvailableVideoZoomFactor, 3))
                device.unlockForConfiguration()
                Task { @MainActor in self.zoom = value }
            } catch { }
        }
    }

    func capture() async throws -> UIImage {
        guard AVCaptureDevice.authorizationStatus(for: .video) == .authorized else { throw CameraError.denied }
        return try await withCheckedThrowingContinuation { continuation in
            queue.async { [weak self] in
                guard let self else { continuation.resume(throwing: CameraError.setupFailed); return }
                let settings = AVCapturePhotoSettings()
                settings.photoQualityPrioritization = .quality
                if self.activeDevice?.hasFlash == true { settings.flashMode = self.flashMode }
                let processor = PhotoProcessor(continuation: continuation)
                processor.onFinish = { [weak self] in self?.processor = nil }
                self.processor = processor
                self.output.capturePhoto(with: settings, delegate: processor)
            }
        }
    }

    private func configure(position: AVCaptureDevice.Position, zoom: CGFloat) {
        guard let device = Self.device(position: position, zoom: zoom) else { return }
        do {
            let newInput = try AVCaptureDeviceInput(device: device)
            session.beginConfiguration()
            session.sessionPreset = .photo
            if let input { session.removeInput(input) }
            if session.canAddInput(newInput) { session.addInput(newInput); input = newInput }
            if !session.outputs.contains(output), session.canAddOutput(output) { session.addOutput(output) }
            if let connection = output.connection(with: .video), connection.isVideoOrientationSupported { connection.videoOrientation = .portrait }
            try? device.lockForConfiguration()
            device.videoZoomFactor = zoom < 1 ? 1 : min(max(zoom, device.minAvailableVideoZoomFactor), min(device.maxAvailableVideoZoomFactor, 3))
            device.unlockForConfiguration()
            session.commitConfiguration()
            activeDevice = device
            Task { @MainActor in
                self.position = position
                self.zoom = zoom
                self.zoomOptions = Self.options(position: position)
                self.isReady = true
            }
        } catch {
            Task { @MainActor in self.isReady = false }
        }
    }

    private static func device(position: AVCaptureDevice.Position, zoom: CGFloat) -> AVCaptureDevice? {
        if position == .back, zoom < 1 {
            return AVCaptureDevice.default(.builtInUltraWideCamera, for: .video, position: .back) ?? AVCaptureDevice.default(.builtInWideAngleCamera, for: .video, position: .back)
        }
        if position == .back {
            return AVCaptureDevice.default(.builtInWideAngleCamera, for: .video, position: .back) ?? AVCaptureDevice.default(.builtInTripleCamera, for: .video, position: .back)
        }
        return AVCaptureDevice.default(.builtInTrueDepthCamera, for: .video, position: .front) ?? AVCaptureDevice.default(.builtInWideAngleCamera, for: .video, position: .front)
    }

    private static func options(position: AVCaptureDevice.Position) -> [CGFloat] {
        guard position == .back else { return [1, 2] }
        return AVCaptureDevice.default(.builtInUltraWideCamera, for: .video, position: .back) == nil ? [1, 2, 3] : [0.5, 1, 2, 3]
    }
}

final class PhotoProcessor: NSObject, AVCapturePhotoCaptureDelegate {
    private let continuation: CheckedContinuation<UIImage, Error>
    var onFinish: (() -> Void)?
    init(continuation: CheckedContinuation<UIImage, Error>) { self.continuation = continuation }

    func photoOutput(_ output: AVCapturePhotoOutput, didFinishProcessingPhoto photo: AVCapturePhoto, error: Error?) {
        defer { onFinish?() }
        if let error { continuation.resume(throwing: error); return }
        guard let data = photo.fileDataRepresentation(), let image = UIImage(data: data) else {
            continuation.resume(throwing: CameraError.captureFailed); return
        }
        continuation.resume(returning: image)
    }
}
