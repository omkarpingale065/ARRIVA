import { useMemo } from 'react';

export default function useNextArrival(trains) {
  return useMemo(() => trains
    .filter((item) => item.predictedArrival && !Number.isNaN(new Date(item.predictedArrival).getTime()))
    .sort((left, right) => new Date(left.predictedArrival) - new Date(right.predictedArrival))[0] ?? trains[0], [trains]);
}
