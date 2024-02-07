import { InstructionCode } from "../core/instruction/InstructionCodes";
import Instruction from "../core/instruction/Instruction";

interface Payload {
    volume: number,
    soundName: string,
    durationMillis: number
}

class PlaySound extends Instruction<Payload> {

    public constructor(soundName: string, volume: number = 100, durationMillis: number = 1000){
        super(InstructionCode.PLAY_SOUND, {
            volume: volume,
            soundName: soundName,
            durationMillis: durationMillis
        })
    }
    
}

export default PlaySound;