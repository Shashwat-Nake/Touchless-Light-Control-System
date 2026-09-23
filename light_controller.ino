// Pin connected to the Relay Module IN pin
const int RELAY_PIN = 8; 

void setup() {
  Serial.begin(9600);
  pinMode(RELAY_PIN, OUTPUT);
  
  // Set default initial state (Relays are often active-low, adjust if needed)
  digitalWrite(RELAY_PIN, LOW); 
}

void loop() {
  if (Serial.available() > 0) {
    char command = Serial.read();
    
    if (command == '1') {
      digitalWrite(RELAY_PIN, HIGH); // Turn Relay / Bulb ON
    } 
    else if (command == '0') {
      digitalWrite(RELAY_PIN, LOW);  // Turn Relay / Bulb OFF
    }
  }
}