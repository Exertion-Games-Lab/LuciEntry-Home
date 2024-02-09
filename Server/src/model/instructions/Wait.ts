import { InstructionCode } from "../core/instruction/InstructionCodes";
import Instruction from "../core/instruction/Instruction";

interface Payload {
    millis: number
}

class Wait extends Instruction<Payload> {

    public constructor(millis: number){
        super(InstructionCode.WAIT, {
            millis: millis 
        })
    }
}

export default Wait;