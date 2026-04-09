import { Pipe, PipeTransform } from '@angular/core';

@Pipe({ name: 'min', standalone: true })
export class MinPipe implements PipeTransform {
  transform(values: number[]): number {
    return Math.min(...values);
  }
}
