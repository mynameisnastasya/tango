# Aesthetic Camera MVP

Original native iOS MVP for an aesthetic composition-camera assistant. It is not a clone of YoungPhoto/Aesthetic Camera: the naming, visual system, overlays and code are original.

## What it does

- Opens a full-screen live camera preview.
- Lets the user choose composition templates in real time.
- Renders guides programmatically with SwiftUI/Canvas, not copied images.
- Captures photos through AVFoundation.
- Shows a result preview.
- Saves clean photos to Photos, with an option to export with guides.
- Includes onboarding, inspiration cards and settings.

## Stack

- Swift
- SwiftUI
- AVFoundation
- Photos / PhotosUI-compatible permissions
- iOS 16+
- MVVM-style state separation
- Local data models, no Firebase/backend

## Project generation

This repository version uses **XcodeGen** so the source code stays clean and text-only in GitHub.

Install XcodeGen once:

```bash
brew install xcodegen
```

Generate the Xcode project:

```bash
cd ios-aesthetic-camera-mvp
xcodegen generate
open AestheticCameraMVP.xcodeproj
```

Then select a real iPhone and run. The Simulator will not show a real camera feed.

## Manual Xcode checks

Because camera apps must be verified on real iOS hardware, check manually:

- camera permission prompt;
- live preview;
- photo capture;
- front/back camera switch;
- flash availability on your device;
- 0.5x ultra-wide support where available;
- saving to Photos;
- signing team and bundle identifier.

## Originality

The app uses the same broad product category idea — camera plus composition help — but avoids copying another app's UI, icon, assets, exact layout, name, branding or proprietary templates.
