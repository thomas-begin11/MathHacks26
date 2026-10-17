#import <Cocoa/Cocoa.h>

// Raylib receives mouse-wheel events on macOS but not NSEventTypeMagnify.
// This tiny bridge collects native trackpad magnification for the Python engine.
static double magnificationDelta = 0.0;
static id magnificationMonitor = nil;

void strife_enable_touchpad_pinch(void) {
    if (magnificationMonitor != nil) return;
    magnificationMonitor = [NSEvent
        addLocalMonitorForEventsMatchingMask:NSEventMaskMagnify
        handler:^NSEvent *(NSEvent *event) {
            magnificationDelta += event.magnification;
            return event;
        }];
}

double strife_take_touchpad_pinch(void) {
    double delta = magnificationDelta;
    magnificationDelta = 0.0;
    return delta;
}
