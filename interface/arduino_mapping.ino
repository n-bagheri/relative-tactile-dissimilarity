
// This code requires the button debounce library
// https://github.com/maykon/ButtonDebounce
// that can be installed from the library manager
// with that library, initialization is "input-pullup" by default,
// which corresponds to our wiring

#include <ButtonDebounce.h>

String message_led_0_on = "led0on";
String message_led_0_off = "led0off";
String message_led_1_on = "led1on";
String message_led_1_off = "led1off";
String message_led_2_on = "led2on";
String message_led_2_off = "led2off";
String message_led_3_on = "led3on";
String message_led_3_off = "led3off";
String message_led_4_on = "led4on";
String message_led_4_off = "led4off";
String message_led_5_on = "led5on";
String message_led_5_off = "led5off";

String message_butPart_0_on = "butp0on";
String message_butPart_0_off = "butp0off";
String message_butPart_1_on = "butp1on";
String message_butPart_1_off = "butp1off";

String message_butXP_0_on = "butx0on";
String message_butXP_0_off = "butx0off";
String message_butXP_1_on = "butx1on";
String message_butXP_1_off = "butx1off";
String message_butXP_2_on = "butx2on";
String message_butXP_2_off = "butx2off";
String message_butXP_3_on = "butx3on";
String message_butXP_3_off = "butx3off";
String message_butXP_4_on = "butx4on";
String message_butXP_4_off = "butx4off";
String message_butXP_5_on = "butx5on";
String message_butXP_5_off = "butx5off";

int debounceDelay = 100;
unsigned long startingTime = 0;
unsigned long currentTime = 0;
bool beforeStartButPushed = true;

byte myLEDs[] = { A0, A1, A2, A3, A4, A5 };
byte myButParticipantPins[] = { 7, 6 };
byte myButExperimenterPins[] = { 9, 12, 13, 8, 10, 11 };

ButtonDebounce myButParticipant_0(myButParticipantPins[0], debounceDelay);
ButtonDebounce myButParticipant_1(myButParticipantPins[1], debounceDelay);
ButtonDebounce myButExperimenter_0(myButExperimenterPins[0], debounceDelay);
ButtonDebounce myButExperimenter_1(myButExperimenterPins[1], debounceDelay);
ButtonDebounce myButExperimenter_2(myButExperimenterPins[2], debounceDelay);
ButtonDebounce myButExperimenter_3(myButExperimenterPins[3], debounceDelay);
ButtonDebounce myButExperimenter_4(myButExperimenterPins[4], debounceDelay);
ButtonDebounce myButExperimenter_5(myButExperimenterPins[5], debounceDelay);

int numLEDs, numButParticipant, numButExperimenter = 0;

//==============================================================================
// the setup routine runs once, at startup
//==============================================================================
void setup() {
  Serial.begin(115200);

  // compute arrays size
  numLEDs = sizeof(myLEDs) / sizeof(myLEDs[0]);
  numButParticipant = sizeof(myButParticipantPins) / sizeof(myButParticipantPins[0]);
  numButExperimenter = sizeof(myButExperimenterPins) / sizeof(myButExperimenterPins[0]);

  // initialize inputs and outputs
  for (int i = 0; i < numLEDs; i++) { pinMode(myLEDs[i], OUTPUT); }

  myButParticipant_0.setCallback(butPart0_Changed);
  myButParticipant_1.setCallback(butPart1_Changed);
  myButExperimenter_0.setCallback(butXP0_Changed);
  myButExperimenter_1.setCallback(butXP1_Changed);
  myButExperimenter_2.setCallback(butXP2_Changed);
  myButExperimenter_3.setCallback(butXP3_Changed);
  myButExperimenter_4.setCallback(butXP4_Changed);
  myButExperimenter_5.setCallback(butXP5_Changed);

  Serial.println("m_init_OK");
}

//==============================================================================
// our specific callbak functions
//==============================================================================
void butPart0_Changed(int state) {
  if (beforeStartButPushed == true) {
    // Serial.println("Participant button 0 changed: " + String(state));
    digitalWrite(myLEDs[0], !state);
  } else {
    currentTime = millis() - startingTime;
    if (state == 0) { Serial.println(message_butPart_0_on +"_"+ String(currentTime)); }
    else if (state == 1) { Serial.println(message_butPart_0_off +"_"+ String(currentTime)); }
  }
}

void butPart1_Changed(int state) {
  if (beforeStartButPushed == true) {
    // Serial.println("Participant button 1 changed: " + String(state));
    digitalWrite(myLEDs[0], !state);
  } else {
    currentTime = millis() - startingTime;
    if (state == 0) { Serial.println(message_butPart_1_on +"_"+ String(currentTime)); }
    else if (state == 1) { Serial.println(message_butPart_1_off +"_"+ String(currentTime)); }
  }
}

void butXP0_Changed(int state) {
  if (beforeStartButPushed == true) {
    // Serial.println("Experimenter button 0 changed: " + String(state));
    digitalWrite(myLEDs[0], !state);
    if (state == 1) {
      startingTime = millis();
      for (int i = 0; i < numLEDs; i++) { digitalWrite(myLEDs[i], LOW); }
      Serial.println("m_XP_starts");
      beforeStartButPushed = false;
    }
  } else {
    currentTime = millis() - startingTime;
    if (state == 0) { Serial.println(message_butXP_0_on +"_"+ String(currentTime)); }
    else if (state == 1) { Serial.println(message_butXP_0_off +"_"+ String(currentTime)); }
  }
}

void butXP1_Changed(int state) {
  if (beforeStartButPushed == true) {
    // Serial.println("Experimenter button 1 changed: " + String(state));
    digitalWrite(myLEDs[1], !state);
  } else {
    currentTime = millis() - startingTime;
    if (state == 0) { Serial.println(message_butXP_1_on +"_"+ String(currentTime)); }
    else if (state == 1) { Serial.println(message_butXP_1_off +"_"+ String(currentTime)); }
  }
}

void butXP2_Changed(int state) {
  if (beforeStartButPushed == true) {
    // Serial.println("Experimenter button 2 changed: " + String(state));
    digitalWrite(myLEDs[2], !state);
  } else {
    currentTime = millis() - startingTime;
    if (state == 0) { Serial.println(message_butXP_2_on +"_"+ String(currentTime)); }
    else if (state == 1) { Serial.println(message_butXP_2_off +"_"+ String(currentTime)); }
  }
}

void butXP3_Changed(int state) {
  if (beforeStartButPushed == true) {
    // Serial.println("Experimenter button 3 changed: " + String(state));
    digitalWrite(myLEDs[3], !state);
  } else {
    currentTime = millis() - startingTime;
    if (state == 0) { Serial.println(message_butXP_3_on +"_"+ String(currentTime)); }
    else if (state == 1) { Serial.println(message_butXP_3_off +"_"+ String(currentTime)); }
  }
}

void butXP4_Changed(int state) {
  if (beforeStartButPushed == true) {
    // Serial.println("Experimenter button 4 changed: " + String(state));
    digitalWrite(myLEDs[4], !state);
  } else {
    currentTime = millis() - startingTime;
    if (state == 0) { Serial.println(message_butXP_4_on +"_"+ String(currentTime)); }
    else if (state == 1) { Serial.println(message_butXP_4_off +"_"+ String(currentTime)); }
  }
}

void butXP5_Changed(int state) {
  if (beforeStartButPushed == true) {
    // Serial.println("Experimenter button 5 changed: " + String(state));
    digitalWrite(myLEDs[5], !state);
  } else {
    currentTime = millis() - startingTime;
    if (state == 0) { Serial.println(message_butXP_5_on +"_"+ String(currentTime)); }
    else if (state == 1) { Serial.println(message_butXP_5_off +"_"+ String(currentTime)); }
  }
}

//==============================================================================
// the loop routine runs over and over again ("forever", and "as often as it's possible")
//==============================================================================
void loop() {
  myButParticipant_0.update();
  myButParticipant_1.update();
  myButExperimenter_0.update();
  myButExperimenter_1.update();
  myButExperimenter_2.update();
  myButExperimenter_3.update();
  myButExperimenter_4.update();
  myButExperimenter_5.update();

  if ( Serial.available() ) {
    String input = Serial.readStringUntil('\n');  // Read until newline
    if (input.equals(message_led_0_on))        { digitalWrite(myLEDs[0], HIGH); }
    else if (input.equals(message_led_0_off))  { digitalWrite(myLEDs[0], LOW); }
    else if (input.equals(message_led_1_on))   { digitalWrite(myLEDs[1], HIGH); }
    else if (input.equals(message_led_1_off))  { digitalWrite(myLEDs[1], LOW); }
    else if (input.equals(message_led_2_on))   { digitalWrite(myLEDs[2], HIGH); }
    else if (input.equals(message_led_2_off))  { digitalWrite(myLEDs[2], LOW); }
    else if (input.equals(message_led_3_on))   { digitalWrite(myLEDs[3], HIGH); }
    else if (input.equals(message_led_3_off))  { digitalWrite(myLEDs[3], LOW); }
    else if (input.equals(message_led_4_on))   { digitalWrite(myLEDs[4], HIGH); }
    else if (input.equals(message_led_4_off))  { digitalWrite(myLEDs[4], LOW); }
    else if (input.equals(message_led_5_on))   { digitalWrite(myLEDs[5], HIGH); }
    else if (input.equals(message_led_5_off))  { digitalWrite(myLEDs[5], LOW); }
    }
}
