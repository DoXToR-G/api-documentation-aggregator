'use client';

import React, { useEffect, useRef, useState } from 'react';

interface GameOfLifeProps {
  cellSize?: number;
  speed?: number;
  density?: number;
  opacity?: number;
}

export default function GameOfLife({
  cellSize = 20,
  speed = 200,
  density = 0.3,
  opacity = 0.15
}: GameOfLifeProps) {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const [isPaused, setIsPaused] = useState(false);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;

    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    // Set canvas size
    const resizeCanvas = () => {
      canvas.width = window.innerWidth;
      canvas.height = window.innerHeight;
    };
    resizeCanvas();
    window.addEventListener('resize', resizeCanvas);

    const cols = Math.floor(canvas.width / cellSize);
    const rows = Math.floor(canvas.height / cellSize);

    // Initialize grid with random cells
    const createGrid = (): boolean[][] => {
      return Array.from({ length: rows }, () =>
        Array.from({ length: cols }, () => Math.random() < density)
      );
    };

    let grid = createGrid();

    // Count alive neighbors
    const countNeighbors = (grid: boolean[][], x: number, y: number): number => {
      let count = 0;
      for (let i = -1; i <= 1; i++) {
        for (let j = -1; j <= 1; j++) {
          if (i === 0 && j === 0) continue;
          const row = (x + i + rows) % rows;
          const col = (y + j + cols) % cols;
          if (grid[row][col]) count++;
        }
      }
      return count;
    };

    // Update grid based on Conway's rules
    const updateGrid = (grid: boolean[][]): boolean[][] => {
      return grid.map((row, x) =>
        row.map((cell, y) => {
          const neighbors = countNeighbors(grid, x, y);
          if (cell) {
            return neighbors === 2 || neighbors === 3;
          } else {
            return neighbors === 3;
          }
        })
      );
    };

    // Draw grid
    const draw = () => {
      ctx.fillStyle = getComputedStyle(document.documentElement)
        .getPropertyValue('--background')
        .trim() ? 'rgb(var(--background))' : '#111827';
      ctx.fillRect(0, 0, canvas.width, canvas.height);

      const isDark = document.documentElement.classList.contains('dark');
      const cellColor = isDark
        ? `rgba(59, 130, 246, ${opacity})` // Blue for dark mode
        : `rgba(79, 70, 229, ${opacity})`; // Indigo for light mode

      grid.forEach((row, x) => {
        row.forEach((cell, y) => {
          if (cell) {
            ctx.fillStyle = cellColor;
            ctx.fillRect(
              y * cellSize,
              x * cellSize,
              cellSize - 1,
              cellSize - 1
            );
          }
        });
      });
    };

    // Animation loop
    let animationId: number;
    let lastUpdate = Date.now();

    const animate = () => {
      const now = Date.now();
      if (!isPaused && now - lastUpdate > speed) {
        grid = updateGrid(grid);
        draw();
        lastUpdate = now;
      }
      animationId = requestAnimationFrame(animate);
    };

    draw();
    animate();

    // Cleanup
    return () => {
      window.removeEventListener('resize', resizeCanvas);
      cancelAnimationFrame(animationId);
    };
  }, [cellSize, speed, density, opacity, isPaused]);

  return (
    <div className="fixed inset-0 -z-10">
      <canvas
        ref={canvasRef}
        className="w-full h-full"
        onClick={() => setIsPaused(!isPaused)}
      />
    </div>
  );
}
