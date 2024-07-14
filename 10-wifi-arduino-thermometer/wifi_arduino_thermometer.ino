//////////////////////////////////////////////////////////////////////////
//////////////////////////////////////////////////////////////////////////
// A Simple Arduino thermometer.
// See https://doc.2minlog.com/tutorials/wifi-arduino-thermometer
//
// Uses NTC thermistor
// - 10 kOhm thermistor connected to A0 and GND
// - 5 kOhm resistor connected to +5V and A0
// Tested for Arduino UNO R4 WiFi
// It sends the results to api.2minlog.com or local server.
//
// This is a simple demo code:
// - Uses linear relationship between voltage and temperature. Logarithmic model is physically more apropriate.
// - Better to use Arduino temperature sensor.
// - Minimal error handling
// - Consider using a watchdog
// - Matrix display with rolling temperature

char ssid[] = "xxxxxxxxxxxxxxxxxx";        // your network SSID (name)
char pass[] = "xxxxxxxxxxxxxxxxxx";   // your network password (use for WPA, or use as key for WEP)
char datasetSecret[] = "SEC-xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx" ;

const int serial_speed = 115200 ;   // You need to set the serial monitor the same speed

char server[] = "api.2minlog.com" ; // Valid options, e.g.: "10.0.0.10", "www.google.com";
int port      = 443; // If 443, it uses HTTPS, otherwise HTTP.
char path[]   = "log" ;

// You need to calibrate your thermometer with those two arrays. Add as many points are you like.
double temperatures[] = { 4.4,   25.4, 30.2 };
double levels[]       = {75.15, 180.9, 200};

#define voltPin A0
const int scroll_speed = 400 ;
const int display_loops = 10 ;

/*
Tutorials:
https://docs.arduino.cc/tutorials/uno-r4-wifi/wifi-examples#wi-fi-web-client-ssl

Reference documentation:
https://www.arduino.cc/reference/en/libraries/wifinina/
*/

#include "WiFiS3.h"
#include "WiFiSSLclient.h"
#include "IPAddress.h"
#include "ArduinoGraphics.h" // You need to install ArduinoGraphcs by Arduino library
#include "Arduino_LED_Matrix.h"

int status = WL_IDLE_STATUS;
Client* client = nullptr ;

ArduinoLEDMatrix matrix;

////////////////////////////////////////////////////////////////////////////////
////////////////////////////////////////////////////////////////////////////////
////////////////////////////////////////////////////////////////////////////////
/////
///// WiFi part
/* -------------------------------------------------------------------------- */
void connect_wifi() {
/* -------------------------------------------------------------------------- */
  // check for the WiFi module:
  if (WiFi.status() == WL_NO_MODULE) {
    Serial.println("Communication with WiFi module failed!");
    // don't continue
    while (true);
  }

  String fv = WiFi.firmwareVersion();
  if (fv < WIFI_FIRMWARE_LATEST_VERSION) {
    Serial.println("Please upgrade the firmware");
  }

  // attempt to connect to WiFi network:
  while (status != WL_CONNECTED) {
    Serial.print("Attempting to connect to SSID: ");
    Serial.println(ssid);
    status = WiFi.begin(ssid, pass);
    delay(10000); // wait 10 seconds for connection:
  }
  printWifiStatus();
}

/* -------------------------------------------------------------------------- */
void difconnect_wifi() {
/* -------------------------------------------------------------------------- */
}

/* -------------------------------------------------------------------------- */
void printWifiStatus() {
/* -------------------------------------------------------------------------- */
  // print the SSID of the network you're attached to:
  Serial.print("SSID: ");
  Serial.println(WiFi.SSID());

  // print your board's IP address:
  IPAddress ip = WiFi.localIP();
  Serial.print("IP Address: ");
  Serial.println(ip);

  // print the received signal strength:
  long rssi = WiFi.RSSI();
  Serial.print("signal strength (RSSI):");
  Serial.print(rssi);
  Serial.println(" dBm");
  Serial.print("Wifi status: ") ;
  Serial.print(WiFi.status()) ;
  Serial.print(" (OK=") ;
  Serial.print(WL_CONNECTED) ;
  Serial.println(")") ;
}

////////////////////////////////////////////////////////////////////////////////
////////////////////////////////////////////////////////////////////////////////
////////////////////////////////////////////////////////////////////////////////
/////
///// HTTP/HTTPs communication

/* -------------------------------------------------------------------------- */
void connect_uri(double level, double temperature) {
/* -------------------------------------------------------------------------- */

  if( client == nullptr )
    if (port == 443) {
      client = new WiFiSSLClient();
    } else {
      client = new WiFiClient();
    }

  Serial.println("\nSetting up connection to server:");
  Serial.println(String(server) + ":" + String(port)) ;

  if (client -> connect(server, port)) {
    Serial.println("Connected to server");

    // HTTP request:
    String query_string = "?datasetSecret=" + String(datasetSecret) ;
    query_string += "&level=" + String(level) ;
    query_string += "&temperature=" + String(temperature) ;

    Serial.println("GET /" + String(path) + String(query_string) + " HTTP/1.1") ;
    client -> println("GET /" + String(path) + String(query_string) + " HTTP/1.1") ;

    Serial.println("Host: " + String(server) + ":" + String(port)) ;
    client -> println("Host: " + String(server) + ":" + String(port)) ;

    Serial.println("Connection: close") ;
    client -> println("Connection: close") ;

    Serial.println() ;
    client -> println() ;

  } else {
    Serial.println("ERROR: Could not connect to the server!");
    delay(5000) ;
  }
}


/* -------------------------------------------------------------------------- */
void disconnect_uri() {
/* -------------------------------------------------------------------------- */
  client -> stop() ;
  // delete client; // There is a memory leakage in the library.
  // client = nullptr;
  Serial.println("Done. Disconnected from the server.");
}


/* -------------------------------------------------------------------------- */
void read_response() {
/* -------------------------------------------------------------------------- */
  Serial.println("About to read the response.");

  while( client -> connected() )
    while (client -> available()) {
      char c = client -> read();
      Serial.print(c);
    }

  Serial.println();

  Serial.println("Response received.");
}

////////////////////////////////////////////////////////////////////////////////
////////////////////////////////////////////////////////////////////////////////
////////////////////////////////////////////////////////////////////////////////
/////
///// Thermometer part

// Least square method temperature = f(level)
/* -------------------------------------------------------------------------- */
double linear_regression_temperature(double level) {
/* -------------------------------------------------------------------------- */
    double sum_T = 0.0, sum_V = 0.0, sum_TV = 0.0, sum_VV = 0.0;

    int n = sizeof(temperatures) / sizeof(temperatures[0]) ;

    for (int i = 0; i < n; ++i) {
        sum_T += temperatures[i];
        sum_V += levels[i];
        sum_TV += temperatures[i] * levels[i];
        sum_VV += levels[i] * levels[i];
    }

    double mean_T = sum_T / n;
    double mean_V = sum_V / n;

    double a = (sum_TV - n * mean_T * mean_V) / (sum_VV - n * mean_V * mean_V);
    double b = mean_T - a * mean_V;

    return a * level + b ;
}


/* -------------------------------------------------------------------------- */
void measure_temperature(double &level, double &temperature) {
/* -------------------------------------------------------------------------- */
  double sum = 0 ;
  int iter = 100 ;

  for(int i = 0 ; i < iter ; i++ ) {
    delay(100) ;
    sum += analogRead(voltPin);
  }

  level = sum / iter ;
  temperature = linear_regression_temperature(level) ;

  Serial.println("**********************");
  Serial.println("Level=");
  Serial.println(level);
  Serial.println("Temperature=");
  Serial.println(temperature);
  Serial.println("**********************");
  Serial.println();

}

////////////////////////////////////////////////////////////////////////////////
////////////////////////////////////////////////////////////////////////////////
////////////////////////////////////////////////////////////////////////////////
/////
///// LED display part
/* -------------------------------------------------------------------------- */
void print_temperature(double temperature, int speed ) {
/* -------------------------------------------------------------------------- */
  char text[16];

  sprintf(text, " %.1f°C ", temperature);

  matrix.stroke(0xFFFFFFFF);
  matrix.textScrollSpeed(speed);

  matrix.textFont(Font_5x7);
  matrix.beginText(0, 1, 0xFFFFFF);
  matrix.println(text);
  matrix.endText(SCROLL_LEFT);
}

/* -------------------------------------------------------------------------- */
void init_draw() {
/* -------------------------------------------------------------------------- */
  const char text[] = "°C!";
  matrix.stroke(0xFFFFFFFF);
  matrix.textFont(Font_4x6);
  matrix.beginText(0, 1, 0xFFFFFF);
  matrix.println(text);
  matrix.endText();
}

////////////////////////////////////////////////////////////////////////////////
////////////////////////////////////////////////////////////////////////////////
////////////////////////////////////////////////////////////////////////////////
/////
///// Arduino setup and loop
/* -------------------------------------------------------------------------- */
void setup() {
/* -------------------------------------------------------------------------- */
  Serial.begin(serial_speed);
  Serial.println("Compiled on " __DATE__ " at " __TIME__);

  matrix.begin();
  matrix.beginDraw();
  init_draw();

  // Always blink the internal LED when reading the temperature
  pinMode(LED_BUILTIN, OUTPUT);
  digitalWrite(LED_BUILTIN, LOW);
}


/* -------------------------------------------------------------------------- */
void loop() {
/* -------------------------------------------------------------------------- */
  double level = 0;
  double temperature = 0 ;

  digitalWrite(LED_BUILTIN, HIGH);
  measure_temperature(level,temperature) ;
  digitalWrite(LED_BUILTIN, LOW);

  connect_wifi() ;
  connect_uri(level, temperature) ;
  read_response() ;
  disconnect_uri() ;
  difconnect_wifi() ;

  for( int i = 0 ; i< display_loops ; i++ ) {
    print_temperature(temperature, scroll_speed ); // Approx. 10 seconds
  }
}
