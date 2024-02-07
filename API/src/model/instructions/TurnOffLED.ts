import { InstructionCode } from "../core/instruction/InstructionCodes";
import Instruction from "../core/instruction/Instruction";

/**
 * Turns off the LED
 */
class TurnOffLED extends Instruction<{}> {

    public constructor(){
        super(InstructionCode.LED_OFF, {});
    }

}

export default TurnOffLED;