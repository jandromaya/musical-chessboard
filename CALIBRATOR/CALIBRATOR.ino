#include <FastLED.h>
#include<float.h>
//#include "calibration.h"

// right now this is set up to work with the small board with just 4 squares

#define LED_PIN 5 //eventually will make this an array (for 8 led strips)
#define NUM_LEDS 8  //LEDs per row
#define LED_TYPE WS2812B
#define NUM_COLORS 6 //red, green, blue, yellow, white, black
#define NUM_ROWS  8
#define OPEN_THRESHOLD 250
#define CLOCK_PIN 13 // pin for the chess clock button

int mux_pins[NUM_ROWS] = {A0, A1, A8, A9, A10, A11, A12, A13};

int mux_chan_pins[NUM_ROWS][3] =
  {
    {8,9,10},
    {31,29,27},
    {38,36,34},
    {44,42,40},
    {46,48,50},
    {51,49,47},
    {45,43,41},
    {39,37,35}
  };

CRGB leds[NUM_LEDS];

// in the future, need to make these 2d arrays
// to identify each ldr individually
float red_on[NUM_ROWS][NUM_LEDS], red_off[NUM_ROWS][NUM_LEDS], red_sig[NUM_ROWS][NUM_LEDS];
float green_on[NUM_ROWS][NUM_LEDS], green_off[NUM_ROWS][NUM_LEDS], green_sig[NUM_ROWS][NUM_LEDS];
float blue_on[NUM_ROWS][NUM_LEDS], blue_off[NUM_ROWS][NUM_LEDS], blue_sig[NUM_ROWS][NUM_LEDS];
float tot_sig[NUM_ROWS][NUM_LEDS];

float min_white_tot[NUM_ROWS][NUM_LEDS];
float max_white_tot[NUM_ROWS][NUM_LEDS];
float min_black_tot[NUM_ROWS][NUM_LEDS];
float max_black_tot[NUM_ROWS][NUM_LEDS];
float min_open_tot[NUM_ROWS][NUM_LEDS];
float max_open_tot[NUM_ROWS][NUM_LEDS];



int lightTime = 50; // delay to let the LDRs catch up to diff colors (ms)

String color[NUM_COLORS + 1] = {"red","green", "blue", "yellow", "orange", "pink", "open"};
// rgb_avg values taken from 50 samples using my modified color_meter_v4

float min_R2[NUM_LEDS][NUM_ROWS];  // Array to store min R² for each LDR

void guess_colors(int guesses[NUM_ROWS][NUM_LEDS]);

void setup() {
  Serial.begin(9600);
  FastLED.addLeds<LED_TYPE, LED_PIN, GRB>(leds, NUM_LEDS).setCorrection( TypicalLEDStrip );
  FastLED.setBrightness(255);
  for (int i = 0; i < NUM_ROWS; i++) {
    for (int j = 0; j < 3; j++) {
      pinMode(mux_chan_pins[i][j], OUTPUT);
    }
  }
  for (int i = 0; i < NUM_ROWS; i++) {
    for (int j = 0; j < NUM_LEDS; j++) {
      min_white_tot[i][j] = FLT_MAX;
      max_white_tot[i][j] = 0;
      min_black_tot[i][j] = FLT_MAX;
      max_black_tot[i][j] = 0;
    }
  }
  pinMode(CLOCK_PIN, INPUT_PULLUP);
}

void loop() {
  float white_sum[NUM_ROWS][NUM_LEDS] = {0};
  float black_sum[NUM_ROWS][NUM_LEDS] = {0};
  float open_sum[NUM_ROWS][NUM_LEDS]  = {0};

  Serial.println("READING WHITE, PRESS BUTTON TO START: ");
  while (digitalRead(CLOCK_PIN) == HIGH) delay(10);
  while (digitalRead(CLOCK_PIN) == LOW) delay(10);

  for (int k = 0; k < 100; k++) {
    read_board();
    for (int i = 0; i < NUM_ROWS; i++) {
      for (int j = 0; j < NUM_LEDS; j++) {
        white_sum[i][j] += tot_sig[i][j];
      }
    }
    Serial.print("WHITE "); Serial.print(k); Serial.println("/100");
  }

  Serial.println("READING BLACK, PRESS BUTTON TO START: ");
  while (digitalRead(CLOCK_PIN) == HIGH) delay(10);
  while (digitalRead(CLOCK_PIN) == LOW) delay(10);

  for (int k = 0; k < 100; k++) {
    read_board();
    for (int i = 0; i < NUM_ROWS; i++) {
      for (int j = 0; j < NUM_LEDS; j++) {
        black_sum[i][j] += tot_sig[i][j];
      }
    }
    Serial.print("BLACK "); Serial.print(k); Serial.println("/100");
  }

  Serial.println("READING OPEN SQUARES, PRESS BUTTON TO START: ");
  while (digitalRead(CLOCK_PIN) == HIGH) delay(10);
  while (digitalRead(CLOCK_PIN) == LOW) delay(10);

  for (int k = 0; k < 100; k++) {
    read_board();
    for (int i = 0; i < NUM_ROWS; i++) {
      for (int j = 0; j < NUM_LEDS; j++) {
        open_sum[i][j] += tot_sig[i][j];
      }
    }
    Serial.print("OPEN "); Serial.print(k); Serial.println("/100");
  }

  float minWhite = FLT_MAX, maxWhite = 0;
  float minBlack = FLT_MAX, maxBlack = 0;
  float minOpen = FLT_MAX, maxOpen = 0;

  Serial.println("\n--- CALIBRATION COMPLETE ---");

  for (int i = 0; i < NUM_ROWS; i++) {
    for (int j = 0; j < NUM_LEDS; j++) {
      float white_avg = white_sum[i][j] / 100.0;
      float black_avg = black_sum[i][j] / 100.0;
      float open_avg  = open_sum[i][j]  / 100.0;

      if (white_avg < minWhite) minWhite = white_avg;
      if (white_avg > maxWhite) maxWhite = white_avg;
      if (black_avg < minBlack) minBlack = black_avg;
      if (black_avg > maxBlack) maxBlack = black_avg;
      if (open_avg < minOpen)   minOpen = open_avg;
      if (open_avg > maxOpen)   maxOpen = open_avg;
    }
  }

  Serial.print("White Avg Min: "); Serial.println(minWhite);
  Serial.print("White Avg Max: "); Serial.println(maxWhite);
  Serial.print("Black Avg Min: "); Serial.println(minBlack);
  Serial.print("Black Avg Max: "); Serial.println(maxBlack);
  Serial.print("Open  Avg Min: "); Serial.println(minOpen);
  Serial.print("Open  Avg Max: "); Serial.println(maxOpen);

    Serial.println("\nPer-Square Averages:\n");

  for (int i = 0; i < NUM_ROWS; i++) {
    for (int j = 0; j < NUM_LEDS; j++) {
      float white_avg = white_sum[i][j] / 100.0;
      float black_avg = black_sum[i][j] / 100.0;
      float open_avg  = open_sum[i][j]  / 100.0;

      Serial.print("Square [");
      Serial.print(i);
      Serial.print("][");
      Serial.print(j);
      Serial.print("] - ");
      Serial.print("White: ");
      Serial.print(white_avg, 2);
      Serial.print(", Black: ");
      Serial.print(black_avg, 2);
      Serial.print(", Open: ");
      Serial.println(open_avg, 2);
    }
  }

}

void read_board() {
  // Light up all LEDs green
  fill_solid(leds, NUM_LEDS, CRGB::Green);
  FastLED.show();
  delay(lightTime);
  for (int row = 0; row < NUM_ROWS; row++) {
    for (int i = 0; i < NUM_LEDS; i++) {
      green_on[row][i] = read_mux(row, i);
    }
  }

  // Turn off all LEDs
  fill_solid(leds, NUM_LEDS, CRGB::Black);
  FastLED.show();
  delay(lightTime);
  for (int row = 0; row < NUM_ROWS; row++) {
    for (int i = 0; i < NUM_LEDS; i++) {
      green_off[row][i] = read_mux(row, i);
    }
  }

  // Light up all LEDs red
  fill_solid(leds, NUM_LEDS, CRGB::Red);
  FastLED.show();
  delay(lightTime);
  for (int row = 0; row < NUM_ROWS; row++) {
    for (int i = 0; i < NUM_LEDS; i++) {
      red_on[row][i] = read_mux(row, i);
    }
  }

  // Turn off all LEDs
  fill_solid(leds, NUM_LEDS, CRGB::Black);
  FastLED.show();
  delay(lightTime);
  for (int row = 0; row < NUM_ROWS; row++) {
    for (int i = 0; i < NUM_LEDS; i++) {
      red_off[row][i] = read_mux(row, i);
    }
  }

  // Light up all LEDs blue
  fill_solid(leds, NUM_LEDS, CRGB::Blue);
  FastLED.show();
  delay(lightTime);
  for (int row = 0; row < NUM_ROWS; row++) {
    for (int i = 0; i < NUM_LEDS; i++) {
      blue_on[row][i] = read_mux(row, i);
    }
  }

  // Turn off all LEDs
  fill_solid(leds, NUM_LEDS, CRGB::Black);
  FastLED.show();
  delay(lightTime);
  for (int row = 0; row < NUM_ROWS; row++) {
    for (int i = 0; i < NUM_LEDS; i++) {
      blue_off[row][i] = read_mux(row, i);
    }
  }

  // Compute color signals
  for (int row = 0; row < NUM_ROWS; row++) {
    for (int i = 0; i < NUM_LEDS; i++) {
      tot_sig[row][i] = (blue_off[row][i] - blue_on[row][i]) +
                        (green_off[row][i] - green_on[row][i]) +
                        (red_off[row][i] - red_on[row][i]);

      if (tot_sig[row][i] != 0) {  // Prevent division by zero
        red_sig[row][i] = 100.0 * (red_off[row][i] - red_on[row][i]) / tot_sig[row][i];
        green_sig[row][i] = 100.0 * (green_off[row][i] - green_on[row][i]) / tot_sig[row][i];
        blue_sig[row][i] = 100.0 * (blue_off[row][i] - blue_on[row][i]) / tot_sig[row][i];
      } else {
        red_sig[row][i] = green_sig[row][i] = blue_sig[row][i] = 0;
      }
    }
  }
}

// Reads the mux indicated by mux_num. Only reads the 
// output channel indicated by channel
int read_mux(int mux_num, int channel) {
   // Convert channel number to binary and set select pins
  int s0 = (channel >> 0) & 1;
  int s1 = (channel >> 1) & 1;
  int s2 = (channel >> 2) & 1;

  digitalWrite(mux_chan_pins[mux_num][0], s0);
  digitalWrite(mux_chan_pins[mux_num][1], s1);
  digitalWrite(mux_chan_pins[mux_num][2], s2);

  return analogRead(mux_pins[mux_num]);
  
}

// void guess_colors(int guesses[NUM_ROWS][NUM_LEDS]) {
//   for (int rows = 0; rows < NUM_ROWS; rows++) {
//     for (int leds = 0; leds < NUM_LEDS; leds++) {
//       float blue_r2 = pow((red_sig[rows][leds] - RGB_AVG[1][0]), 2) +
//                       pow((green_sig[rows][leds] - RGB_AVG[1][1]), 2) +
//                       pow((blue_sig[rows][leds] - RGB_AVG[1][2]), 2);
//       float red_r2 = pow((red_sig[rows][leds] - RGB_AVG[0][0]), 2) +
//                      pow((green_sig[rows][leds] - RGB_AVG[0][1]), 2) +
//                      pow((blue_sig[rows][leds] - RGB_AVG[0][2]), 2);
//       if (red_r2 < blue_r2) {
//         guesses[rows][leds] = -1;
//       }
//       else {
//         guesses[rows][leds] = 1;
//       }
//       if (tot_sig[rows][leds] < OPEN_THRESHOLD) {
//         guesses[rows][leds] = 0;
//       }
//     }
//   }
// }