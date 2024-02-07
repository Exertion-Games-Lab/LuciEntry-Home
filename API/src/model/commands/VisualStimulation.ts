import Command from "../core/command/Command";
import TurnOffLED from "../instructions/TurnOffLED";
import TurnOnLED from "../instructions/TurnOnLED";
import Wait from "../instructions/Wait";
import { CommandName } from "../core/command/CommandNames";
import { Colour } from "../instructions/utils/Colour";

class VisualStimulation extends Command {

    public brightness?: number;
    public colour?: Colour;

    public constructor(brightness?: number, colour?: Colour){
        
        super(CommandName.VISUAL_STIMULUS, []);

        this.generateInstructions(colour, brightness);
        this.brightness = brightness;
        this.colour = colour;
    }

    public generateInstructions(colour?: Colour, brightness?: number){
        const flashCount = 10;
        const flashRate = 1000;
        const instructions = [];

        for (let i=0; i<flashCount; i++){
            instructions.push(new TurnOnLED(colour || new Colour(255, 0, 0), brightness || 100));
            instructions.push(new Wait(flashRate));
            instructions.push(new TurnOffLED());
            instructions.push(new Wait(flashRate));
        }

        this.instructions = instructions;
    }

    public setPayload(payload: any): void {
        if (typeof payload !== "object") return;

        if ('brightness' in payload){
            if (typeof payload.brightness === "number"){
                this.brightness = payload.brightness;
            } else {
                console.error("Brightness must be of type number")
            }
        }

        if ('colour' in payload){
            if ('r' in payload.colour && 'g' in payload.colour && 'b' in payload.colour){
                if (typeof payload.colour.r === "number" && typeof payload.colour.g === "number" && typeof payload.colour.b === "number"){
                    this.colour = new Colour(payload.colour.r, payload.colour.g, payload.colour.b)
                } else {
                    console.error("rgb values must be a number")
                }
            }
        }

        this.generateInstructions(this.colour, this.brightness);
    }

    public clone(): VisualStimulation {
        return new VisualStimulation(
            this.brightness,
            this.colour
        )
    }

}

export default VisualStimulation;
