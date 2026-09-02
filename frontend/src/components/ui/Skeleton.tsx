import React from 'react';
import { clsx } from 'clsx';
import { twMerge } from 'tailwind-merge';

interface SkeletonProps {
  className?: string;
  count?: number;
}

export const Skeleton: React.FC<SkeletonProps> = ({ className, count = 1 }) => {
  return (
    <>
      {Array.from({ length: count }).map((_, i) => (
        <div
          key={i}
          className={twMerge(
            clsx(
              'animate-pulse bg-slate-200/80 rounded-md',
              className
            )
          )}
        />
      ))}
    </>
  );
};
