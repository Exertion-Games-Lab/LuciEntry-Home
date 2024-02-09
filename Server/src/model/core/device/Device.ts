import Command from "../command/Command";
import CommandMap from "../command/Commands";

/**
 * Holds the information for our device, including the commands
 */
class Device {

    public readonly id: string;
    private _commands: Command[] = [];

    public constructor(id: string){
        this.id = id;
    }

    public get commands(): Command[] {
        return this._commands;
    }

    public clearCommands(){
        this._commands = [];
    }
    
    /**
     * Tries to add a command
     * @param commandName the name of the command to add or the command
     * @returns true if success
     */
    public addCommand(command: string | Command, payload?: any): boolean {
        const newCommand: Command | undefined = (typeof command == "string") ? CommandMap.get(command)?.clone() : command;
        
        newCommand?.setPayload(payload || {});

        if (newCommand == undefined){
            console.error(`Could not find command`);
            return false
        }
            
        this._commands.push(newCommand);

        return true;
    }

    public deleteCommand(id: string){
        this._commands = this._commands.filter(c => c.id != id);
    }

    /**
     * Gets the next command for this device
     * @returns is undefined if there are no commands
     */
    public getNextCommand(): Command | undefined {
        const command = this._commands.shift();
        return command;
    }

}

export default Device;