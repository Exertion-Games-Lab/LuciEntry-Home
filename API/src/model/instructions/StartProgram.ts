import Instruction from "../core/instruction/Instruction";
import { InstructionCode } from "../core/instruction/InstructionCodes";

interface Payload {
    programNumber: number
}

export class StartProgram extends Instruction<Payload> {

    public constructor(programNumber: number){
        super(InstructionCode.START_PROGRAM, {
            programNumber: programNumber
        })
    }

}