#include <windows.h>
#include <mmdeviceapi.h>
#include <endpointvolume.h>
#include <iostream>

int main() {
    HRESULT hr = CoInitialize(NULL);
    if (FAILED(hr)) {
        std::cerr << "CoInitialize failed" << std::endl;
        return 1;
    }

    IMMDeviceEnumerator* deviceEnumerator = NULL;
    hr = CoCreateInstance(__uuidof(MMDeviceEnumerator), NULL, CLSCTX_INPROC_SERVER, __uuidof(IMMDeviceEnumerator), (LPVOID*)&deviceEnumerator);
    if (FAILED(hr)) {
        std::cerr << "CoCreateInstance failed" << std::endl;
        CoUninitialize();
        return 1;
    }

    IMMDevice* defaultDevice = NULL;
    hr = deviceEnumerator->GetDefaultAudioEndpoint(eRender, eConsole, &defaultDevice);
    if (FAILED(hr)) {
        std::cerr << "GetDefaultAudioEndpoint failed" << std::endl;
        deviceEnumerator->Release();
        CoUninitialize();
        return 1;
    }

    IAudioEndpointVolume* endpointVolume = NULL;
    hr = defaultDevice->Activate(__uuidof(IAudioEndpointVolume), CLSCTX_INPROC_SERVER, NULL, (LPVOID*)&endpointVolume);
    if (FAILED(hr)) {
        std::cerr << "Activate failed" << std::endl;
        defaultDevice->Release();
        deviceEnumerator->Release();
        CoUninitialize();
        return 1;
    }

    float currentVolume = 0.0f;
    hr = endpointVolume->GetMasterVolumeLevelScalar(&currentVolume);
    if (FAILED(hr)) {
        std::cerr << "GetMasterVolumeLevelScalar failed" << std::endl;
        endpointVolume->Release();
        defaultDevice->Release();
        deviceEnumerator->Release();
        CoUninitialize();
        return 1;
    }

    std::cout << currentVolume << std::endl;

    endpointVolume->Release();
    defaultDevice->Release();
    deviceEnumerator->Release();
    CoUninitialize();
    return 0;
}
