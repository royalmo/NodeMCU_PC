#include <ESP8266WiFi.h>

//NETWORK SETTINGS
const char* ssid = "Fibracat_16052";
const char* password = "243dcab8cb";
IPAddress ip(192, 168, 1, 19);
IPAddress gateway(192, 168, 1, 0);
IPAddress subnet(255, 255, 255, 0);

//SETTING GPIOs PORTS (different from marked on board)
const int PCled = 14; //D5
const int PCbut = 05; //D1
const int FANs1 = 12; //D6
const int FANs2 = 13; //D7
const int PCstt = 00; //D3
const int Relay = 15; //D8
const int Buzzer = 04; //D2
WiFiServer server(80);

//SETTING GLOBAL VARIABLES
int i = 0;
int a = 0;
int PCstatus = 0;
int FANstatus = 0;
int RELAYstatus = 0;

void setup() {
  // Serial for future testing.
  //Serial.begin(115200);
  delay(10);

  // Declare pins.
  pinMode(PCstt, OUTPUT);
  pinMode(Relay, OUTPUT);
  pinMode(Buzzer, OUTPUT);
  digitalWrite(PCstt, LOW);
  digitalWrite(Relay, LOW);
  pinMode(PCled, INPUT_PULLUP);
  pinMode(PCbut, INPUT_PULLUP);
  pinMode(FANs1, INPUT_PULLUP);
  pinMode(FANs2, INPUT_PULLUP);
 
  // Connect to WiFi network, and start the server.
  //Serial.println("Welcome, connecting to wifi.");
  WiFi.config(ip, gateway, subnet);
  WiFi.begin(ssid, password);
  while (WiFi.status() != WL_CONNECTED) {
    delay(50);
  }
  //Serial.println("WiFi connected.");
  server.begin();
  //Serial.println("Server started. You can connect to it at http://192.168.1.19/"); 
}
 
void loop() {
  // Check physic inputs
  digitalWrite(PCstt, not(digitalRead(PCbut))); //Check PCbut.
  if (digitalRead(PCbut) == LOW and RELAYstatus == 0){//Turns on relay if needed.
    RELAYstatus = 1;
    digitalWrite(Relay, HIGH);
  }
  PCstatus = not(digitalRead(PCled)); //Updates PCstatus.
  if (digitalRead(FANs1) == LOW){ //Update FANstatus.
    FANstatus = 2; //Only command-startup allowed.
  }
  else if(digitalRead(FANs2) == LOW){
    FANstatus = 0; //Everything allowed.
  }
  else{
    FANstatus = 1; //Command allowed, but restinged web.
  }
  if ((PCstatus == 0 and RELAYstatus == 1) and digitalRead(PCbut) == HIGH){ //Turn off relay, if needed.
     if (a==1000) {
      digitalWrite(Relay, LOW);
      RELAYstatus = 0;
     }
     else {
      a++;
     }
  }
  else {
    a = 0;
  }
  
  // Check if a client has connected
  WiFiClient client = server.available();
  if (!client) {
    return;
  }
  // Wait until the client sends some data (if he sends some)
  //Serial.println("New client");
  i = 0;
  while(!client.available()){
    if (i == 100){
      //Serial.println("Fake client");
      client.flush();
      return;
    }
    i++;
    delay(1);
  }
  // Read the first line of the request
  String request = client.readStringUntil('\r');
  //Serial.println(request);
  client.flush();
  // Match the request
  if (request.indexOf("/status") != -1)  {
    client.println("HTTP/1.1 200 OK");
    client.println("Content-Type: text/plain");
    client.println(""); // IMPORTANT
    client.print("PCstatus: ");
    client.println(PCstatus);
    client.print("FANstatus: ");
    client.println(FANstatus);
    client.print("RELAYstatus: ");
    client.println(RELAYstatus);
    client.print("BUTstatus: ");
    client.println(not(digitalRead(PCbut)));
  }
  else if (request.indexOf("/pcstart") != -1)  {
    if (PCstatus == 1){
      client.println("HTTP/1.1 200 OK");
      client.println("Content-Type: text/plain");
      client.println(""); // IMPORTANT
      client.println("Error: PC is already on!");
    }
    else {
      RELAYstatus = 1;
      digitalWrite(Relay, HIGH);
      delay(500);
      digitalWrite(PCstt, HIGH);
      tone(Buzzer, 880);
      delay(500);
      digitalWrite(PCstt, LOW);
      noTone(Buzzer);
      client.println("HTTP/1.1 200 OK");
      client.println("Content-Type: text/plain");
      client.println(""); // IMPORTANT
      client.println("Done! Check status to verify it yourself.");
    }
  }
  else if (request.indexOf("/favicon.ico") != -1)  {
    client.println("HTTP/1.1 404 NO ICON");
    client.println("");
  }
  else if (request.indexOf("/shutdown") != -1)  {
    client.println("HTTP/1.1 200 OK");
    client.println("Content-Type: text/plain");
    client.println(""); // IMPORTANT
    if (FANstatus == 2){
      client.println("Error: You don't have the permissions to do this!");
    }
    else if (PCstatus == 1){
      digitalWrite(PCstt, HIGH);
      tone(Buzzer, 880);
      client.println("Done! Check status to verify it yourself.");
      delay(500);
      digitalWrite(PCstt, LOW);
      noTone(Buzzer);
    }
    else {
      client.println("Error: PC is already off!");
    }
  }
  else if (request.indexOf("/forceshutdown") != -1)  {
    client.println("HTTP/1.1 200 OK");
    client.println("Content-Type: text/plain");
    client.println(""); // IMPORTANT
    if (FANstatus != 0){
      client.println("Error: You don't have the permissions to do this!");
    }
    else if (PCstatus == 1){
      digitalWrite(PCstt, HIGH);
      tone(Buzzer, 880);
      client.println("Done! Check status to verify it yourself.");
      delay(6000);
      digitalWrite(PCstt, LOW);
      noTone(Buzzer);
      delay(1000);
      digitalWrite(Relay, LOW);
      delay(500);
    }
    else {
      client.println("Error: PC is already off!");
    }
  }
  else {
    client.println("HTTP/1.1 200 OK");
    client.println("Content-Type: text/html");
    client.println(""); // IMPORTANT
    client.println("<html>");
    client.println("<h1>Eric's PC config</h1>");
    client.println("<br>");
    client.println("<p>To control this device, you need to go to the raspberry's page on http://192.168.1.20/ with the good codes.</p>");
    client.println("</html>");
  }
  //Serial.println("Client disonnected");
  //Serial.println("");
}
 
