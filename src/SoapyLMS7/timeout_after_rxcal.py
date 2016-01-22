import SoapySDR
from SoapySDR import * #SOAPY_SDR_* constants

import numpy as np

import matplotlib.pyplot as plt

import time
import threading

def threadToPeriodicallyHitSettings(streamBoardSDR):
    print("="*50)
    print("== Triggering CalibrateRx() in 10 secs...")
    print("="*50)
    time.sleep(10)
    t0 = time.time()
    streamBoardSDR.setGain(SOAPY_SDR_RX, 0, "LNA", 10.0)
    t1 = time.time()
    print("="*50)
    print("== Total CalibrateRx() time -- %f secs"%(t1-t0))
    print("="*50)

if __name__ == '__main__':
    streamBoardSDR = SoapySDR.Device({"driver":"lime"})

    print("Set master clock rate")
    streamBoardSDR.setMasterClockRate(32e6)
    print streamBoardSDR.getMasterClockRate()/1e6, "MHz"

    print("Tune the LOs")
    streamBoardSDR.setFrequency(SOAPY_SDR_RX, 0, "RF", 1e9)
    streamBoardSDR.setFrequency(SOAPY_SDR_TX, 0, "RF", 1e9)

    print("Tune cordics")
    streamBoardSDR.setFrequency(SOAPY_SDR_RX, 0, "BB", 50e3)
    streamBoardSDR.setFrequency(SOAPY_SDR_RX, 1, "BB", 50e3)
    streamBoardSDR.setFrequency(SOAPY_SDR_TX, 0, "BB", 0.0)
    streamBoardSDR.setFrequency(SOAPY_SDR_TX, 1, "BB", 0.0)

    print("Pick sample rates")
    streamBoardSDR.setSampleRate(SOAPY_SDR_RX, 0, 32e6/8)
    streamBoardSDR.setSampleRate(SOAPY_SDR_RX, 1, 32e6/8)
    streamBoardSDR.setSampleRate(SOAPY_SDR_TX, 0, 32e6/8)
    streamBoardSDR.setSampleRate(SOAPY_SDR_TX, 1, 32e6/8)

    print("Set RX gains")
    streamBoardSDR.setGain(SOAPY_SDR_RX, 0, "LNA", 10.0)
    streamBoardSDR.setGain(SOAPY_SDR_RX, 0, "TIA", 12.0)
    streamBoardSDR.setGain(SOAPY_SDR_RX, 0, "PGA", -3.0)
    streamBoardSDR.setGain(SOAPY_SDR_RX, 1, "LNA", 10.0)
    streamBoardSDR.setGain(SOAPY_SDR_RX, 1, "TIA", 12.0)
    streamBoardSDR.setGain(SOAPY_SDR_RX, 1, "PGA", -3.0)

    streamBoardSDR.setDCOffsetMode(SOAPY_SDR_RX, 0, False)
    streamBoardSDR.setDCOffsetMode(SOAPY_SDR_RX, 1, False)

    print("set RX bandwidth")
    streamBoardSDR.setAntenna(SOAPY_SDR_RX, 0, "LNAL")
    streamBoardSDR.setAntenna(SOAPY_SDR_RX, 1, "LNAL")
    t0 = time.time()
    streamBoardSDR.setBandwidth(SOAPY_SDR_RX, 0, 10e6)
    streamBoardSDR.setBandwidth(SOAPY_SDR_RX, 1, 10e6)
    t1 = time.time()
    print("="*50)
    print("== Total RxA&B filter cal time -- %f secs"%(t1-t0))
    print("="*50)

    print("Create rx stream")
    rxStream = streamBoardSDR.setupStream(SOAPY_SDR_RX, SOAPY_SDR_CF32, [0, 1])
    streamBoardSDR.activateStream(rxStream)

    print("Test receive")
    sampsCh0 = np.array([0]*1024, np.complex64)
    sampsCh1 = np.array([0]*1024, np.complex64)

    streamBoardSDR.writeSetting("ACTIVE_CHANNEL", "A");
    streamBoardSDR.writeSetting("ENABLE_RXTSP_CONST", "true");
    streamBoardSDR.writeSetting("ACTIVE_CHANNEL", "B");
    streamBoardSDR.writeSetting("ENABLE_RXTSP_CONST", "true");

    settingsThread = threading.Thread(target=threadToPeriodicallyHitSettings, args=[streamBoardSDR])
    settingsThread.start()

    totalSamps = 0
    timeLastPrint = time.time()
    hadTimeout = False
    while True:
        sr = streamBoardSDR.readStream(rxStream, [sampsCh0, sampsCh1], sampsCh0.size, timeoutUs=int(1e6))
        if sr.ret < 1:
            hadTimeout = True
            print("TIMEOUT duration >>> %f secs !!! <<<"%(time.time()-timeLastRecv))
        else:
            totalSamps += sr.ret
            timeLastRecv = time.time()
            if time.time() > timeLastPrint + 1.0:
                print(">>> OK RECEIVE %f: %d"%(time.time(), totalSamps))
                timeLastPrint = time.time()
                if hadTimeout: break

    settingsThread = None

    """
    for i in range(1000):
        sr = streamBoardSDR.readStream(rxStream, [sampsCh0, sampsCh1], sampsCh0.size, 0)
        if i == 0: print 'sr0', sr
        if i == 1: print 'sr1', sr
        if sr.ret < 1:
            print sr
            break
        totalSamps += sr.ret

    print sr
    print "totalSamps", totalSamps

    plt.plot(np.real(sampsCh0[:32]), label="ChA:I")
    plt.plot(np.imag(sampsCh0[:32]), label="ChA:Q")
    plt.plot(np.real(sampsCh1[:32]) + .1, label="ChB:I")
    plt.plot(np.imag(sampsCh1[:32]) + .1, label="ChB:Q")
    plt.legend()
    plt.ylabel('some numbers')
    plt.show()
    """

    print("Cleanup rx stream")
    streamBoardSDR.deactivateStream(rxStream)
    streamBoardSDR.closeStream(rxStream)
