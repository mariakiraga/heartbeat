/*
 * KY039 Pulse Detector
 * Detects individual heartbeat pulses from an analog sensor.
 * Outputs "BEAT" over Serial on each detected rising edge.
 */

#define SAMPLE_WINDOW_MS  20    // Duration of each averaging window (filters 50Hz mains noise)
#define ROLLING_AVG_SIZE  6     // Number of windows to smooth over (filters motion artifacts)
#define RISE_THRESHOLD    6     // Consecutive rising windows required to confirm a beat

const int SENSOR_PIN = A0;

void setup() {
    Serial.begin(115200);
}

void loop() {
    float windowAvgs[ROLLING_AVG_SIZE];  // Circular buffer of recent window averages
    float rollingSum = 0;
    float rollingAvg = 0;
    float prevAvg = 0;

    int bufferPtr = 0;
    int riseCount = 0;
    bool rising = false;

    // Initialise circular buffer to zero
    for (int i = 0; i < ROLLING_AVG_SIZE; i++) windowAvgs[i] = 0;

    while (1) {
        // Average many reads over SAMPLE_WINDOW_MS
        float windowSum = 0;
        int sampleCount = 0;
        long windowStart = millis();

        do {
            windowSum += analogRead(SENSOR_PIN);
            sampleCount++;
        } while (millis() < windowStart + SAMPLE_WINDOW_MS);

        float windowAvg = windowSum / sampleCount;

        // Rolling average over last N windows
        // Smooths slower noise like finger movement or inconsistent pressure.
        rollingSum -= windowAvgs[bufferPtr];
        rollingSum += windowAvg;
        windowAvgs[bufferPtr] = windowAvg;
        rollingAvg = rollingSum / ROLLING_AVG_SIZE;

        bufferPtr = (bufferPtr + 1) % ROLLING_AVG_SIZE;

        // Rising edge detection
        // A beat is confirmed when the smoothed signal rises consistently
        // for RISE_THRESHOLD consecutive windows. The 'rising' flag
        // prevents the same beat from triggering multiple times.
        if (rollingAvg > prevAvg) {
            riseCount++;
            if (!rising && riseCount > RISE_THRESHOLD) {
                rising = true;
                Serial.println("BEAT");
            }
        } else {
            rising = false;
            riseCount = 0;
        }

        prevAvg = rollingAvg;
    }
}