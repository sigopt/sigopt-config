/* eslint-disable no-console */
import readline from "readline";

import ConfigBroker from "../src/js/sigopt_config/broker";

const readlineInterface = readline.createInterface({
  input: process.stdin,
  output: process.stdout,
  terminal: false,
});

let dispatchP = Promise.resolve(null);
let configBroker = null;

const loadConfigBroker = ({directory}) => {
  dispatchP = dispatchP.then(() => {
    return ConfigBroker.fromDirectory(directory).then(
      (broker) => {
        configBroker = broker;
        console.log(
          JSON.stringify({message: `Loaded broker from ${directory}`}),
        );
      },
      (err) => {
        console.log(
          JSON.stringify({
            error: `Error loading broker from ${directory}: ${err}`,
          }),
        );
        console.error(err);
      },
    );
  });
};

const readConfigBroker = ({key}) => {
  dispatchP = dispatchP.then(() => {
    if (!configBroker) {
      console.log(
        JSON.stringify({error: `Error reading from broker: broker not loaded`}),
      );
      return;
    }
    try {
      const value = configBroker.get(key);
      console.log(JSON.stringify({value}));
      return;
    } catch (err) {
      console.log(JSON.stringify({error: `Error reading from broker: ${err}`}));
      console.error(err);
      return;
    }
  });
};

const resetConfigBroker = () => {
  dispatchP = dispatchP.then(() => {
    configBroker = null;
    console.log(JSON.stringify({message: "Reset the broket, ready to load"}));
  });
};

readlineInterface.on("line", (line) => {
  let command;
  try {
    command = JSON.parse(line);
  } catch (err) {
    console.log(
      JSON.stringify({error: `Could not parse JSON command: ${line}`}),
    );
    console.error(err);
    return;
  }
  const runCommand = {
    load: loadConfigBroker,
    get: readConfigBroker,
    reset: resetConfigBroker,
    done: () => {
      console.log(JSON.stringify({}));
      process.exit();
    },
  }[command.command];
  if (!runCommand) {
    console.log(JSON.stringify({error: `Unknown command: ${command.command}`}));
    return;
  }
  runCommand(command);
});
