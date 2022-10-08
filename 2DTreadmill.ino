const byte numChars = 32;
char receivedChars[numChars];   // an array to store the received data

const unsigned int MAX_COMMAND_LENGTH = 100;
#define SPTR_SIZE   20
char   *sPtr [SPTR_SIZE];
signed long number;

boolean newData = false;
unsigned long trigger_delay_x = 0;
unsigned long trigger_delay_y = 0;

double stepper_delay_x = 1000;
double stepper_delay_y = 1000;

double pid_x_val = 0;
double pid_y_val = 0;

int dev_x = 0;
int dev_y = 0;

int dead_band = 5; // if the absolute PID response is smaller than this value, stop all motors.

#include <PIDController.h>
PIDController pid_x;
PIDController pid_y;

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

  pid_x.begin();          // initialize the PID instance
  pid_x.setpoint(0);    // The "goal" the PID controller tries to "reach"
  pid_x.tune(10, 8, 3);    // Tune the PID, arguments: kP, kI, kD
  pid_x.limit(-6400, 6400);    // Limit the PID output

  pid_y.begin();          // initialize the PID instance
  pid_y.setpoint(0);    // The "goal" the PID controller tries to "reach"
  pid_y.tune(10, 8, 3);    // Tune the PID, arguments: kP, kI, kD
  pid_y.limit(-6400, 6400);    // Limit the PID output  
}

void loop() {
  // check for new inputs & process them
  recvWithEndMarker();
  processNewData();

  // switch the motor orientation with sign switches
  if (stepper_delay_x >= 0){
    digitalWrite(52, HIGH);
  } else {
    digitalWrite(52, LOW);
  }
  
  if (micros() >= trigger_delay_x){
    trigger_delay_x += stepper_delay_x;
    if (abs(pid_x_val) >= dead_band){
      digitalWrite(53, LOW);
      digitalWrite(53, HIGH);
    }
  }

  // switch the motor orientation with sign switches
  if (stepper_delay_y >= 0){
    digitalWrite(2, HIGH);
  } else {
    digitalWrite(2, LOW);
  }
  
  if (micros() >= trigger_delay_y){
    trigger_delay_y += stepper_delay_y;
    if (abs(pid_y_val) >= dead_band){
      digitalWrite(3, LOW);
      digitalWrite(3, HIGH);
    }
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

void processNewData() {
    if (newData == true) {
        int N = separate (receivedChars, sPtr, SPTR_SIZE);

        dev_x = atoi(sPtr [1]);
        Serial.print("New stepper delays: X ");
        Serial.print(sPtr [1]);

        pid_x_val = pid_x.compute(dev_x);
        stepper_delay_x = 6400 / pid_x_val;

        Serial.print("  new x_delay: ");
        Serial.print(stepper_delay_x);

        dev_y = atoi(sPtr [3]);
        Serial.print(" , Y ");
        Serial.print(sPtr [3]);

        pid_y_val = pid_x.compute(dev_y);
        stepper_delay_x = 6400 / pid_y_val;

        Serial.print("  new y_delay: ");
        Serial.println(stepper_delay_y);

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
