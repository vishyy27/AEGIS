export class EventSequencer {
  private sequenceNumber = 0;

  public validateSequence(incomingSeq: number): boolean {
    if (incomingSeq <= this.sequenceNumber) return false; // Stale or duplicate
    this.sequenceNumber = incomingSeq;
    return true;
  }
}
export const eventSequencer = new EventSequencer();
