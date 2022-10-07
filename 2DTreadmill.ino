const byte numChars = 32;
char receivedChars[numChars];   // an array to store the received data

const unsigned int MAX_COMMAND_LENGTH = 100;
#define SPTR_SIZE   20
char   *sPtr [SPTR_SIZE];
signed long number;

boolean newData = false;
unsigned long trigger_delay_x = 0;
unsigned long trigger_delay_y = 0;

int stepper_delay_x = 1000;
int stepper_delay_y = 1000;

int dev_x = 1000;
int dev_y = 1000;

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
    trigger_delay_y += stepper_delay_y;
  }

  if (micros() >= trigger_delay_x){
    digitalWrite(53, LOW);
    digitalWrite(53, HIGH);
    trigger_delay_x += stepper_delay_x;
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
        int N = separate (receivedChars, sPtr, SPTR_SIZE);

        dev_x = atoi(sPtr [1]);
        Serial.print("New stepper delays: X ");
        Serial.print(sPtr [1]);

        dev_y = atoi(sPtr [3]);
        Serial.print(" , Y ");
        Serial.println(sPtr [3]);

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
