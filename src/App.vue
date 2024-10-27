<!-- eslint-disable @typescript-eslint/no-unused-vars -->
<script setup lang="ts">
import { onMounted, onUnmounted, ref, useTemplateRef } from "vue";

// export type Board = Array<Array<string | number>>;

type MoveDirection = "left" | "right" | "none";

type Coordinates = { x: number; y: number };

type Brick = {
  problem: string;
  colour: string;
  size: number;
  step: number;
  hit?: boolean;
};

//****** data ******

const bricks: Array<Array<Brick>> = [
  [
    {
      problem: "(λx. (λy. * y 2) ((λy. * y 2) x)) 5",
      size: 69,
      step: 1,
      colour: "seashell",
    },
    {
      problem: "(λy. * y 2) ((λ. * y 2)) 5)",
      size: 100,
      step: 2,
      colour: "lightpink",
    },
  ],
  [
    { problem: "* ((λy. * y 2) 5) 2", size: 100, step: 3, colour: "lavender" },
    { problem: "* (* 5 2) 2", size: 300, step: 4, colour: "whitesmoke" },
  ],
];

let currentProblem = ref("(λf. λx. f (f x)) (λy. * y 2) 5");
let nextStep = 1;

let message: string | null = null;

//******************

// const bricks: Array<Array<Brick>> = [[]];

const canvas = useTemplateRef("gameCanvas");
const canvasWidth = 1200;
const canvasHeight = 600;

const moveStep = 10;
let moveDirection: MoveDirection = "none";

const solutions = ref();

let paddlePosX = canvasWidth / 2;
const paddleWidth = 300;
const paddlePosY = 550;
const paddleHeight = 10;

let ballPosX = 420;
let ballPosY = 420;
let ballVelocityX = 1;
let ballVelocityY = 1;
let ballSize = 10;
let ballMoveStep = 4;

let mousePos: { x: number; y: number } = { x: 0, y: 0 };

let isFire = false;
let isFiringMode = true;

const brickHeight = 45;

let gameInterval: number;

function getMousePosition(event: MouseEvent): { x: number; y: number } {
  const c = canvas.value!;
  const rect = c.getBoundingClientRect();
  const scaleX = c.width / rect.width;
  const scaleY = c.height / rect.height;

  return {
    x: (event.clientX - rect.left) * scaleX,
    y: (event.clientY - rect.top) * scaleY,
  };
}

function drawBricks() {
  const ctx = canvas.value!.getContext("2d")!;
  let row = 0;
  for (const bricksInRow of bricks.slice().reverse()) {
    const totalLength = bricksInRow.reduce((acc, val) => (acc += val.size), 0);
    const scaleFactor = canvasWidth / totalLength;

    let startX = 0;
    for (const brick of bricksInRow) {
      if (!brick.hit) {
        ctx.beginPath();
        ctx.rect(
          startX,
          row * brickHeight,
          brick.size * scaleFactor,
          brickHeight
        );
        ctx.fillStyle = brick.colour;
        ctx.fill();
        ctx.closePath();

        ctx.font = "25px sans-serif";
        ctx.fillStyle = "black";
        ctx.textAlign = "center";
        ctx.fillText(
          brick.problem,
          startX + (brick.size * scaleFactor) / 2,
          (row + 1) * brickHeight - 10
        );
      }

      startX += brick.size * scaleFactor;
    }

    row++;
  }
}

function drawPaddle() {
  const ctx = canvas.value!.getContext("2d")!;
  ctx.beginPath();
  ctx.rect(paddlePosX - paddleWidth / 2, paddlePosY, paddleWidth, paddleHeight);
  ctx.fillStyle = "#ffffff";
  ctx.fill();
  ctx.closePath();
}

function drawBall() {
  const ctx = canvas.value!.getContext("2d")!;
  ctx.beginPath();
  ctx.arc(ballPosX, ballPosY, ballSize, 0, 2 * Math.PI);
  ctx.fillStyle = "#ffffff";
  ctx.fill();
  ctx.closePath();
}

function drawMessage() {
  if (message) {
    const ctx = canvas.value!.getContext("2d")!;
    ctx.font = "25px sans-serif";
    ctx.fillStyle = "white";
    ctx.textAlign = "center";
    ctx.fillText(message, canvasWidth / 2, canvasHeight / 2);
  }
}

function drawRay() {
  const ctx = canvas.value!.getContext("2d")!;

  const x = mousePos.x + (mousePos.x - ballPosX) * 1000;
  const y = mousePos.y + (mousePos.y - ballPosY) * 1000;

  ctx.beginPath();
  ctx.moveTo(ballPosX, ballPosY);
  ctx.strokeStyle = "white";
  ctx.lineTo(x, y);
  ctx.stroke();
}

function processMovement() {
  let delta = 0;
  if (moveDirection === "left") {
    delta = -moveStep;
  } else if (moveDirection === "right") {
    delta = moveStep;
  }
  paddlePosX = Math.max(0, Math.min(canvasWidth, paddlePosX + delta));
}

function processBallMovement() {
  ballPosX += ballMoveStep * ballVelocityX;
  ballPosY += ballMoveStep * ballVelocityY;
}

function intersects(
  bbox: { fromX: number; fromY: number; toX: number; toY: number },
  now: Coordinates,
  future: Coordinates
): [boolean, boolean] {
  let intersectsX: boolean = false;
  let intersectsY: boolean = false;

  if (
    now.y > bbox.fromY &&
    now.y < bbox.toY &&
    (now.x < bbox.fromX || now.x > bbox.toX) &&
    future.x > bbox.fromX &&
    future.x < bbox.toX
  ) {
    intersectsX = true;
  }

  if (
    now.x > bbox.fromX &&
    now.x < bbox.toX &&
    (now.y < bbox.fromY || now.y > bbox.toY) &&
    future.y > bbox.fromY &&
    future.y < bbox.toY
  ) {
    intersectsY = true;
  }

  return [intersectsX, intersectsY];
}

function doIntersectsWithBall(
  bbox: { fromX: number; fromY: number; toX: number; toY: number },
  now: Coordinates,
  future: Coordinates
) {
  const [hitsX, hitsY] = intersects(bbox, now, future);

  if (hitsX) {
    ballVelocityX = -ballVelocityX;
  }

  if (hitsY) {
    ballVelocityY = -ballVelocityY;
  }
}

function processPaddleIntersection() {
  const fromX = paddlePosX - paddleWidth / 2;
  const fromY = paddlePosY - paddleHeight / 2;
  const toX = paddlePosX + paddleWidth / 2;
  const toY = paddlePosY + paddleHeight / 2;

  const nextStepX = ballPosX + ballMoveStep * ballVelocityX;
  const nextStepY = ballPosY + ballMoveStep * ballVelocityY;

  const [hitsX, hitsY] = intersects(
    { fromX, fromY, toX, toY },
    { x: ballPosX, y: ballPosY },
    { x: nextStepX, y: nextStepY }
  );

  if (hitsY) {
    const x = ballPosX - paddlePosX;
    const y = ballPosY - 60 - paddlePosY;

    const xSquared = x * x;
    const ySquared = y * y;
    const hSquared = xSquared + ySquared;

    const h = Math.sqrt(hSquared);

    const velocityX = x / h;
    const velocityY = y / h;

    ballVelocityX = velocityX * 2.5;
    ballVelocityY = velocityY * 2.5;
  }
}

function processBrickIntersection() {
  const nextStepX = ballPosX + ballMoveStep * ballVelocityX;
  const nextStepY = ballPosY + ballMoveStep * ballVelocityY;

  let row = 0;
  for (const bricksInRow of bricks.slice().reverse()) {
    const totalLength = bricksInRow.reduce((acc, val) => (acc += val.size), 0);
    const scaleFactor = canvasWidth / totalLength;

    let startX = 0;
    for (const brick of bricksInRow) {
      if (!brick.hit) {
        const bbox = {
          fromX: startX,
          fromY: row * brickHeight,
          toX: startX + brick.size * scaleFactor,
          toY: (row + 1) * brickHeight,
        };

        if (
          nextStepX > bbox.fromX &&
          nextStepX < bbox.toX &&
          nextStepY > bbox.fromY &&
          nextStepY < bbox.toY
        ) {
          ballVelocityY = -ballVelocityY;

          if (nextStep === brick.step) {
            brick.hit = true;
            currentProblem.value = brick.problem;
            ++nextStep;
          } else {
            alert("wrong!!!!!!");
          }
        }
      }

      startX += brick.size * scaleFactor;
    }
    row++;
  }
}

function processWallIntersection() {
  const nextStepX = ballPosX + ballMoveStep * ballVelocityX;
  const nextStepY = ballPosY + ballMoveStep * ballVelocityY;

  if (nextStepX > canvasWidth || nextStepX < 0) {
    ballVelocityX = -ballVelocityX;
  }

  if (nextStepY > canvasHeight || nextStepY < 0) {
    ballVelocityY = -ballVelocityY;
  }
}

function tick() {
  const ctx = canvas.value!.getContext("2d")!;
  ctx.clearRect(0, 0, canvasWidth, canvasHeight);

  processMovement();

  if (!isFiringMode) {
    message = null;

    processPaddleIntersection();
    processBrickIntersection();
    processWallIntersection();
    processBallMovement();
  } else {
    message = "Use left-click to fire";

    ballPosX = paddlePosX;
    ballPosY = paddlePosY - 10;

    drawRay();

    if (isFire) {
      isFire = false;
      isFiringMode = false;

      const x = mousePos.x - ballPosX;
      const y = mousePos.y - ballPosY;

      const xSquared = x * x;
      const ySquared = y * y;
      const hSquared = xSquared + ySquared;

      const h = Math.sqrt(hSquared);

      const velocityX = x / h;
      const velocityY = y / h;

      ballVelocityX = velocityX * 2.5;
      ballVelocityY = velocityY * 2.5;
    }
  }

  drawBricks();
  drawPaddle();
  drawBall();
  drawMessage();
}

function start() {
  addEventListener("keydown", (event) => {
    if (event.key === "a") {
      moveDirection = "left";
    }
    if (event.key === "d") {
      moveDirection = "right";
    }
  });
  addEventListener("keyup", (event) => {
    if (
      (moveDirection === "left" && event.key === "a") ||
      (moveDirection === "right" && event.key == "d")
    ) {
      moveDirection = "none";
    }
  });

  canvas.value!.addEventListener("mousemove", (event) => {
    mousePos = getMousePosition(event);
  });

  canvas.value!.addEventListener("click", (event) => {
    if (isFiringMode) isFire = true;
  });

  gameInterval = setInterval(tick, 16);
}

onMounted(start);
onUnmounted(() => {
  clearInterval(gameInterval);
});
</script>

<template>
  <div id="canvas-container">
    <h1>β-reduction breakout</h1>
    <canvas
      ref="gameCanvas"
      :width="canvasWidth"
      :height="canvasHeight"
    ></canvas>

    <h2>Current problem</h2>
    <div id="current-problem">
      <div class="problem">
        <span class="expression">{{ currentProblem }}</span>
        <span class="symbol">↦<sub>β</sub></span> <span class="what">?</span>
      </div>
    </div>
  </div>
</template>

<style scoped>
#canvas-container {
  width: 100%;
  text-align: center;
  color: white;
  font-family: sans-serif;
}
#current-problem {
  background-color: #333333;
  border: white solid 1px;
  font-size: 40px;
  margin: 0 auto;
  display: inline-block;
  padding: 1rem;
}
canvas {
  display: block;
  margin: 0 auto;
  background-color: #333333;
  border: white solid 1px;
}
.problem {
  display: flex;
  gap: 1rem;
}
.symbol {
  font-weight: 400;
}
.expression {
  color: yellow;
}
.what {
  font-weight: 700;
}
</style>
