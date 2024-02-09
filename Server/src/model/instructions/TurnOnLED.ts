import { InstructionCode } from "../core/instruction/InstructionCodes";
import Instruction from "../core/instruction/Instruction";
import { Colour } from "./utils/Colour";

interface Payload {
    brightness: number,
    colour: {
        r: number,
        g: number,
        b: number
    }
}

/**
 * Turns on the LED for a specific colour and brightness
 */
class TurnOnLED extends Instruction<Payload> {

    public constructor(colour: Colour = new Colour(255, 0, 0), brightness: number = 100){
        super(InstructionCode.LED_ON, {
            brightness: brightness,
            colour: colour.getColour()
        });
    }

}

export default TurnOnLED;