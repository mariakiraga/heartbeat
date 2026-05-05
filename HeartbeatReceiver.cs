/*
using System;
using System.Net;
using System.Net.Sockets;
using System.Text;
using System.Threading;
using Bhaptics.SDK2;
using UnityEngine;

public class HeartbeatReceiver : MonoBehaviour
{
    private Thread receiveThread;
    private UdpClient client;
    private int port = 5005;

    // Flagi używane do komunikacji między wątkiem UDP a głównym wątkiem Unity
    private bool triggerStrongBeat = false;
    private bool triggerWeakBeat = false;

    // Tablice intensywności dla 40 silników
    private int[] strongBeatPattern = new int[40];
    private int[] weakBeatPattern = new int[40];

    void Start()
    {
        SetupSpatialPatterns();
        StartReceiving();
        Debug.Log("Unity nasłuchuje sygnałów bicia serca na porcie " + port);
    }

    private void SetupSpatialPatterns()
    {
        // Indeksy na przodzie kamizelki X40 (0-19)
        // Rząd 1: 0  1  2  3  4
        // Rząd 2: 5  6  7  8  9  <-- tu celujemy (lewa/środek klatki)
        // Rząd 3: 10 11 12 13 14
        // Rząd 4: 15 16 17 18 19

        // --- WZÓR SILNEGO UDERZENIA ---
        // Epicentrum (lewa pierś - max moc)
        strongBeatPattern[6] = 100;
        strongBeatPattern[11] = 100;

        // Pierścień wewnętrzny (rozchodzenie się - średnia moc)
        strongBeatPattern[1] = 60; strongBeatPattern[2] = 60;
        strongBeatPattern[5] = 60; strongBeatPattern[7] = 60;
        strongBeatPattern[10] = 60; strongBeatPattern[12] = 60;

        // Pierścień zewnętrzny (słaba moc)
        strongBeatPattern[0] = 20; strongBeatPattern[3] = 20; strongBeatPattern[8] = 20;
        strongBeatPattern[13] = 20; strongBeatPattern[15] = 20; strongBeatPattern[16] = 20; strongBeatPattern[17] = 20;

        // --- WZÓR SŁABEGO UDERZENIA ---
        // Zachowujemy ten sam kształt, ale z mniejszą ogólną mocą
        for (int i = 0; i < 40; i++)
        {
            weakBeatPattern[i] = (int)(strongBeatPattern[i] * 0.5f); // 50% mocy silnego uderzenia
        }
    }

    private void StartReceiving()
    {
        receiveThread = new Thread(new ThreadStart(ReceiveData));
        receiveThread.IsBackground = true;
        receiveThread.Start();
    }

    private void ReceiveData()
    {
        client = new UdpClient(port);
        IPEndPoint anyIP = new IPEndPoint(IPAddress.Any, 0);

        try
        {
            while (true)
            {
                byte[] data = client.Receive(ref anyIP);
                string text = Encoding.UTF8.GetString(data);

                // Sprawdzamy co przyszło z Pythona
                if (text == "BEAT_STRONG")
                {
                    triggerStrongBeat = true;
                }
                else if (text == "BEAT_WEAK")
                {
                    triggerWeakBeat = true;
                }
            }
        }
        catch (Exception err)
        {
            Debug.Log(err.ToString());
        }
    }

    void Update()
    {
        // Unity API bHaptics musi być wywoływane w głównym wątku (Update)
        if (triggerStrongBeat)
        {
            BhapticsLibrary.PlayMotors((int)PositionType.Vest, strongBeatPattern, 150); // Krótkie: 150ms
            triggerStrongBeat = false;
        }

        if (triggerWeakBeat)
        {
            BhapticsLibrary.PlayMotors((int)PositionType.Vest, weakBeatPattern, 100); // Bardzo krótkie: 100ms
            triggerWeakBeat = false;
        }
    }

    void OnApplicationQuit()
    {
        // Zatrzymujemy wątek UDP przy wyłączaniu gry, żeby uniknąć wycieków pamięci/zablokowanych portów
        if (receiveThread != null && receiveThread.IsAlive)
        {
            receiveThread.Abort();
        }
        if (client != null)
        {
            client.Close();
        }
    }
}
*/

using System;
using System.Net;
using System.Net.Sockets;
using System.Text;
using System.Threading;
using Bhaptics.SDK2;
using UnityEngine;

public class HeartbeatReceiver : MonoBehaviour
{
    private Thread receiveThread;
    private UdpClient client;
    private int port = 5005;

    private bool triggerBeat = false;

    // 40-motor intensity pattern for the bHaptics X40 vest.
    // Front panel layout (indices 0-19):
    //   Row 1:  0  1  2  3  4
    //   Row 2:  5  6  7  8  9
    //   Row 3: 10 11 12 13 14
    //   Row 4: 15 16 17 18 19
    private int[] beatPattern = new int[40];

    void Start()
    {
        SetupPattern();
        StartReceiving();
        Debug.Log("HeartbeatReceiver listening on UDP port " + port);
    }

    private void SetupPattern()
    {
        // Epicentre: left chest (where the heart sits)
        beatPattern[6] = 100;
        beatPattern[11] = 100;

        // Inner ring: medium intensity radiating outward
        beatPattern[1] = 60;
        beatPattern[2] = 60;
        beatPattern[5] = 60;
        beatPattern[7] = 60;
        beatPattern[10] = 60;
        beatPattern[12] = 60;

        // Outer ring: low intensity for spatial spread
        beatPattern[0] = 20;
        beatPattern[3] = 20;
        beatPattern[8] = 20;
        beatPattern[13] = 20;
        beatPattern[15] = 20;
        beatPattern[16] = 20;
        beatPattern[17] = 20;
    }

    private void StartReceiving()
    {
        receiveThread = new Thread(ReceiveData) { IsBackground = true };
        receiveThread.Start();
    }

    private void ReceiveData()
    {
        client = new UdpClient(port);
        IPEndPoint anyIP = new IPEndPoint(IPAddress.Any, 0);
        try
        {
            while (true)
            {
                byte[] data = client.Receive(ref anyIP);
                string text = Encoding.UTF8.GetString(data).Trim();
                if (text == "BEAT")
                    triggerBeat = true;
            }
        }
        catch (Exception e)
        {
            Debug.Log("HeartbeatReceiver error: " + e);
        }
    }

    void Update()
    {
        // bHaptics API must be called from the main Unity thread
        if (triggerBeat)
        {
            BhapticsLibrary.PlayMotors((int)PositionType.Vest, beatPattern, 150);
            Debug.Log("BEAT");
            triggerBeat = false;
        }
    }

    void OnApplicationQuit()
    {
        receiveThread?.Abort();
        client?.Close();
    }
}