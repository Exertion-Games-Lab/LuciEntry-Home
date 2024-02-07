import Command from "../core/command/Command";
import { CommandName } from "../core/command/CommandNames";
import TurnOffLED from "../instructions/TurnOffLED";
import TurnOnLED from "../instructions/TurnOnLED";
import Wait from "../instructions/Wait";

class AirPump extends Command {

    private millis: number;

    public constructor(millis: number = 10000){
        super(CommandName.AIR_PUMP, []);
        this.millis = millis;
        this.generateInstructions();
    }

    public clone(): Command {
        return new AirPump(this.millis);
    }

    public generateInstructions(){
        this.instructions = [
            new TurnOnLED(),
            new Wait(this.millis),
            new TurnOffLED()
        ]
    }

    public setPayload(payload: any): void {
        if (typeof payload === "object"){
            if ('millis' in payload){
                if (typeof payload.millis === "number"){
                    this.millis = payload.millis;
                }else{
                    console.error("Millis must be of type number")
                }
            }
        }

        this.generateInstructions();
    }

}

export default AirPump;