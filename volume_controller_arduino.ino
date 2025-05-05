const int potentiometer1Pin = A0;
const int potentiometer2Pin = A1; 
const int potentiometer3Pin = A2;
const int potentiometer4Pin = A3; 

void setup() {
  Serial.begin(9600); 
}

void loop() {
 
  int pot1Value = analogRead(potentiometer1Pin);
  int pot2Value = analogRead(potentiometer2Pin);
  int pot3Value = analogRead(potentiometer3Pin);
  int pot4Value = analogRead(potentiometer4Pin);

 
  int volume1 = map(pot1Value, 0, 1023, 0, 100);
  int volume2 = map(pot2Value, 0, 1023, 0, 100);
  int volume3 = map(pot3Value, 0, 1023, 0, 100);
  int volume4 = map(pot4Value, 0, 1023, 0, 100);

 
  Serial.print(volume1);
  Serial.print(",");
  Serial.print(volume2);
  Serial.print(",");
  Serial.print(volume3);
  Serial.print(",");
  Serial.println(volume4);

  delay(100); 
}

