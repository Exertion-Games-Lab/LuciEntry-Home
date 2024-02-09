import Command from "../core/command/Command";
import PlaySound from "../instructions/PlaySound";
import { CommandName } from "../core/command/CommandNames";

class Audio extends Command {

    public volume?: number;
    public duration?: number;
    public filename?: string;

    public constructor(volume?: number, duration?: number, filename?: string){
        super(CommandName.AUIDO, [
            new PlaySound(filename || "", volume || 100, duration || 10000),
        ])

        this.volume = volume;
        this.duration = duration;
        this.filename = filename;
    }

    public generateInstructions(){
        this.instructions = [
            new PlaySound(this.filename || "", this.volume || 100, this.duration || 10000)
        ]
    }

    public setPayload(payload: any): void {
        if (typeof payload === "object"){
            if ('filename' in payload){
                if (typeof payload.filename === "string"){
                    this.filename = payload.filename;
                } else {
                    console.error("Filename must be a string");
                }
            }

            if ('volume' in payload){
                if (typeof payload.volume === "number"){
                    this.volume = payload.volume;
                }else{
                    console.error("Volume must be of type number");
                }
            }
    
            if ('duration' in payload){
                if (typeof payload.duration === "number"){
                    this.duration = payload.duration;
                }else{
                    console.error("Volume must be of type number")
                }
            }
        }

        this.generateInstructions();
    }
    
    public clone(): Audio {
        return new Audio(
            this.volume,
            this.duration,
            this.name
        )
    }
}

export default Audio;