import { InstructionCode } from "../core/instruction/InstructionCodes";
import Instruction from "../core/instruction/Instruction";


class StopTACS extends Instruction<{}> {

    public constructor(){
        super(InstructionCode.STOP_TACS, {});
    }

}

export default StopTACS;
