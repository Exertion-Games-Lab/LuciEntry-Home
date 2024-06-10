import { InstructionCode } from "../core/instruction/InstructionCodes";
import Instruction from "../core/instruction/Instruction";

interface Payload {
    intensity: number,
    frequency: number
}

class StartTACS extends Instruction<Payload> {

    public constructor(intensity: number = 255, frequency: number =  255){
        super(InstructionCode.START_TACS, {
            intensity:intensity,
            frequency: frequency
        })
    }
    
}

export default StartTACS;
