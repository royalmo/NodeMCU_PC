#include <ESP8266WiFi.h>

/*   THIS CODE IS FOR CONTROLLING REMOTELY A PC, WITH A NODE-MCU BOARD. Look at README.md
 * ========================================================================================
 * Made by Eric Roy. Check more info and copyright at https://github.com/royalmo/NodeMCU_PC
 *  */

//NETWORK SETTINGS (Things that you have to change)
const char* ssid = "**************"; //Put your LAN settings.
const char* password = "**********";
IPAddress ip(192, 168, 1, 99); //Define the best settings for you. I putted example IPs.
IPAddress gateway(192, 168, 1, 0);
IPAddress subnet(255, 255, 255, 0);
IPAdress raspberry_ip(192, 168, 1, 24); //You need to configure the raspberry's static IP on the board or the router.

//GLOBAL VARIABLES
WiFiServer server(80);
WiFiClient client;
String request;
unsigned long timeCheck = 0;

//SETTING GPIOs PORTS (different from marked on board)
const int PCsensor = 14; //D5
const int CASEbut = 05; //D1
const int FANs1 = 12; //D6
const int FANs2 = 13; //D7
const int PCstartBUT = 00; //D3
const int Relay = 15; //D8
const int Buzzer = 04; //D2

void WIFIconnect() {
  WiFi.begin(ssid, password);
  while (WiFi.status() != WL_CONNECTED) {
    delay(1);
  }
}

bool newClient(){
  //Checks if a new client has connected, and so, if the sketch can continue.
  client = server.available();
  if (!client) {
    return 1;
  }
  unsigned long start_time = millis();;
  while(!client.available()){
    if ((start_time + 100) < millis()){
      client.flush();
      return 1;
      //Fake client (Chrome for desktop does this a lot).
    }
    delay(1);
  }
  request = client.readStringUntil('\r');
  client.flush();
  return 0;
}

void checkUnplug(){
  if (not(PCvalue()) and RELAYvalue()){
     if (timeCheck > 7000){
      digitalWrite(Relay, LOW);
      timeCheck = 0;
     }
     else {
      timeCheck++;
      delay(1);
     }
  }
  else {
    timeCheck = 0;
  }
}

void PCstart() {
  //Sequence for starting the computer.
  digitalWrite(Relay, HIGH);
  delay(400);
  digitalWrite(PCstartBUT, HIGH);
  delay(400);
  digitalWrite(PCstartBUT, LOW);
}

void PCshutdown() {
  digitalWrite(PCstartBUT, HIGH);
  tone(Buzzer, 880);
  delay(500);
  digitalWrite(PCstartBUT, LOW);
  noTone(Buzzer);
}

void FORCEshutdown(){
  //Sequence for shuting down the computed, in forced mode.
  digitalWrite(PCstartBUT, HIGH);
  tone(Buzzer, 880);
  delay(6000);
  digitalWrite(PCstartBUT, LOW);
  noTone(Buzzer);
  delay(5000);
  digitalWrite(Relay, LOW);
}

int caseBut() {
  if (digitalRead(CASEbut)){
    return false;
  }
  delay(100);
  return not(digitalRead(CASEbut));
}

int FANvalue() {
  //Checks FAN value.
  if (digitalRead(FANs1) == LOW){
    //Only command-startup allowed.
    return 0;
  }
  else if(digitalRead(FANs2) == LOW){
    //Everything is allowed.
    return 2;
  }
  else{
    //Command allowed except forced shutdown, but only startup via web.
    return 1;
  }
}

int PCvalue() {
  //Checks PC status
  return not(digitalRead(PCsensor));
}

int RELAYvalue() {
  //Returns Relay value
  return digitalRead(Relay);
}

void PRINTmessage(int code, bool from_bot = false, bool shutdown = false){
  //This function prints obligatory header for http response, and the response depending on the code given.
  client.println("HTTP/1.1 200 OK");
  client.println("Content-Type: text/plain");
  client.println(""); // IMPORTANT
  if (from_bot) {
    client.println(String(code));
    if (shutdown) {
      client.println("S") + String(FANvalue()));
      return void;
    }
    code = 6;
  }
  switch (code) {
    case 0 :
      client.println("Done! Check status to verify it yourself.");
      break;
    case 1 :
      client.println("Error: PC is already off!");
      break;
    case 2 :
      client.println("Error: PC is already on!");
      break;
    case 3 :
      client.println("Error: You don't have the permissions to do this!");
      break;
    case 4 :
      client.println("PCstatus: " + String(PCvalue()) + " FANvalue: " + String(FANvalue()));
      break;
    case 5 :
      client.println("Eric's PC controller.\nTo control this device, you need to go to the webs with the good codes.");
      break;
    case 6 :
      client.println(String(PCvalue()) + String(FANvalue()));
      break;
  }
}

void setup() {
  // DECLARE PINS
  pinMode(PCstartBUT, OUTPUT);
  pinMode(Relay, OUTPUT);
  pinMode(Buzzer, OUTPUT);
  digitalWrite(PCstartBUT, LOW);
  digitalWrite(Relay, LOW);
  pinMode(PCsensor, INPUT_PULLUP);
  pinMode(CASEbut, INPUT_PULLUP);
  pinMode(FANs1, INPUT_PULLUP);
  pinMode(FANs2, INPUT_PULLUP);

  // CONNECT TO NETWORK.
  WiFi.setAutoReconnect(true);
  WiFi.config(ip, gateway, subnet);
  WIFIconnect();
  server.begin();
}

void loop() {
  // MANUAL CASE BUTTON UPDATE.
  if (caseBut()) {
    if (not(RELAYvalue())) {
      PCstart();
    }
    else {
      while (not(digitalRead(CASEbut))){
        digitalWrite(PCstartBUT, HIGH);
        delay(1);
      }
      digitalWrite(PCstartBUT, LOW);
    }
  }

  // CHECK IF RELAY CAN BE TURNED OFF
  checkUnplug();

  // LOOK FOR A CLIENT AND REQUEST
  if (newClient()){
    return;
  }

  //CHECK IF CLIENT IS THE RASPBERRY
  if (client.remoteIP() != raspberry_ip) {
    PRINTmessage(5);
    return;
  }

  // MAKE REQUEST
  if (request.indexOf("/status") != -1)  {
    PRINTmessage(4);
  }
  if (request.indexOf("/data") != -1)  {
    PRINTmessage(6);
  }
  else if (request.indexOf("/telegramstart") != -1)  {
    if (PCvalue()){
      PRINTmessage(2, true);
    }
    else if (FANvalue() == 2) {
      PRINTmessage(3, true);
    }
    else {
      tone(Buzzer, 880);
      PCstart();
      noTone(Buzzer);
      PRINTmessage(0, true);
    }
  }
  else if (request.indexOf("/start") != -1)  {
    if (PCvalue()){
      PRINTmessage(2);
    }
    else {
      tone(Buzzer, 880);
      PCstart();
      noTone(Buzzer);
      PRINTmessage(0);
    }
  }
  else if (request.indexOf("/telegramshutdown") != -1)  {
    if (FANvalue() == 0 & PCvalue()){
      PCshutdown();
      PRINTmessage(0, true, true);
    }
    else if (not(PCvalue())){
      PRINTmessage(1, true);
    }
    else {
      PRINTmessage(3, true);
    }
  }
  else if (request.indexOf("/shutdown") != -1)  {
    if (FANvalue() == 2){
      PRINTmessage(3);
    }
    else if (PCvalue()){
      PCshutdown();
      PRINTmessage(0);
    }
    else {
      PRINTmessage(1);
    }
  }
  else if (request.indexOf("/forceshutdown") != -1)  {
    if (FANvalue() != 0){
      PRINTmessage(3);
    }
    else if (PCvalue()){
      FORCEshutdown();
      PRINTmessage(0);
    }
    else {
      PRINTmessage(1);
    }
  }
  else {
    PRINTmessage(5);
  }
}
