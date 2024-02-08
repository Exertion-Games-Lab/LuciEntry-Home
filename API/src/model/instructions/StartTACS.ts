import { InstructionCode } from "../core/instruction/InstructionCodes";
import Instruction from "../core/instruction/Instruction";

interface Payload {
    intensity: number,
}

class StartTACS extends Instruction<Payload> {

    public constructor(intensity: number = 255){
        super(InstructionCode.START_TACS, {
            intensity:intensity
        })
    }
    
}

export default StartTACS;
