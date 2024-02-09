import { InstructionCode } from "../core/instruction/InstructionCodes";
import Instruction from "../core/instruction/Instruction";

class StopSound extends Instruction<{}> {

    public constructor(){
        super(InstructionCode.STOP_SOUND, {});
    }

}

export default StopSound;