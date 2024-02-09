import Instruction from "../core/instruction/Instruction";
import { InstructionCode } from "../core/instruction/InstructionCodes";

interface Payload {
    programNumber: number
}

export class StopProgram extends Instruction<Payload> {

    public constructor(programNumber: number){
        super(InstructionCode.STOP_PROGRAM, {
            programNumber: programNumber
        })
    }

}