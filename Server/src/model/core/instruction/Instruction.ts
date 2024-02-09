import { InstructionCode } from './InstructionCodes'

/**
 * This is our base instruction class, extend this to create new instructions for commands. 
 * P is the type of payload, you can define any payload type you want, but it must stay consistent for the instance of instruction.
 */
abstract class Instruction<P> {

    public code: InstructionCode;
    public payload: P;

    public constructor(code: InstructionCode, payload: P){
        this.code = code;
        this.payload = payload;
    }

}

export default Instruction;