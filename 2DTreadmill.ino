int stepper_delay = 1000;
const byte numChars = 32;
char receivedChars[numChars];   // an array to store the received data

boolean newData = false;
unsigned long trigger_delay_x = 0;
unsigned long trigger_delay_y = 0;

void setup() {
  // start communication
  Serial.begin(115200);

  // Y axis
  pinMode(2, OUTPUT);
  pinMode(3, OUTPUT);
  digitalWrite(2, HIGH);

  // X axis
  pinMode(52, OUTPUT);
  pinMode(53, OUTPUT);
  digitalWrite(52, HIGH);
}

void loop() {
  recvWithEndMarker();
  showNewData();

  if (micros() >= trigger_delay_y){ 
    digitalWrite(3, LOW);
    digitalWrite(3, HIGH);
    trigger_delay_y += stepper_delay;
  }

  if (micros() >= trigger_delay_x){
    digitalWrite(53, LOW);
    digitalWrite(53, HIGH);
    trigger_delay_x += stepper_delay;
  }

}

void recvWithEndMarker() {
    static byte ndx = 0;
    char endMarker = '\n';
    char rc;
    
    while (Serial.available() > 0 && newData == false) {
        rc = Serial.read();

        if (rc != endMarker) {
            receivedChars[ndx] = rc;
            ndx++;
            if (ndx >= numChars) {
                ndx = numChars - 1;
            }
        }
        else {
            receivedChars[ndx] = '\0'; // terminate the string
            ndx = 0;
            newData = true;
        }
    }
}

void showNewData() {
    if (newData == true) {
        if (atoi(receivedChars) > 0){
          stepper_delay = atoi(receivedChars);
          Serial.print("New stepper delay: ");
          Serial.println(receivedChars);
        } else {
          Serial.println("Invalid command! Integers only, please!");
        }
        newData = false;
    }
}

int separate (String str, char **p, int size)
{
    int  n;
    char s [100];

    strcpy (s, str.c_str ());

    *p++ = strtok (s, " ");
    for (n = 1; NULL != (*p++ = strtok (NULL, " ")); n++)
        if (size == n)
            break;

    return n;
}
