export class StreamValidator {
  public validate(event: any): boolean {
    if (!event || typeof event !== 'object') return false;
    if (!event.type) return false;
    return true;
  }
}
export const streamValidator = new StreamValidator();
