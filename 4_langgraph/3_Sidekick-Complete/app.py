import gradio as gr
from sidekick import Sidekick


async def setup():
    sidekick = Sidekick()
    await sidekick.setup()
    return sidekick

async def process_message(sidekick, message, success_criteria, history):
    results = await sidekick.run_superstep(message, success_criteria, history)
    return results, sidekick
    
async def reset():
    new_sidekick = Sidekick()
    await new_sidekick.setup()
    return "", "", None, new_sidekick

def free_resources(sidekick):
    print("Cleaning up")
    try:
        if sidekick:
            sidekick.free_resources()
    except Exception as e:
        print(f"Exception during cleanup: {e}")


# Create the main Gradio interface using Blocks layout with a custom title and emerald theme
# The Blocks interface provides more flexibility than the simple Interface for complex layouts
with gr.Blocks(title="Sidekick", theme=gr.themes.Default(primary_hue="emerald")) as ui:
    # Display a markdown header introducing the application
    # This creates a prominent title for the Sidekick Personal Co-Worker interface
    gr.Markdown("## Sidekick Personal Co-Worker")
    
    # Create a state component to store the Sidekick instance throughout the session
    # The delete_callback parameter ensures proper cleanup when the component is destroyed
    # This prevents resource leaks by calling free_resources() when the UI is closed
    sidekick = gr.State(delete_callback=free_resources)
    
    # Create a row layout for the main chat interface
    # Rows in Gradio arrange components horizontally for better space utilization
    with gr.Row():
        # Create a chatbot component to display the conversation history
        # The height=300 parameter sets a fixed height for the chat area
        # type="messages" creates a modern message-based chat interface
        chatbot = gr.Chatbot(label="Sidekick", height=300, type="messages")
    
    # Group related input components together for better organization
    # Groups help visually separate different sections of the interface
    with gr.Group():
        # Create a row for the main message input field
        with gr.Row():
            # Text input box for user requests to the Sidekick
            # show_label=False removes the label to save space
            # placeholder provides helpful text when the field is empty
            message = gr.Textbox(show_label=False, placeholder="Your request to the Sidekick")
        
        # Create another row for the success criteria input
        with gr.Row():
            # Text input box for defining success criteria for the task
            # This allows users to specify what constitutes a successful completion
            # Note: There's a typo in "critiera" - should be "criteria"
            success_criteria = gr.Textbox(show_label=False, placeholder="What are your success critiera?")
    
    # Create a row for action buttons at the bottom of the interface
    with gr.Row():
        # Reset button to clear the conversation and start fresh
        # variant="stop" gives it a red appearance to indicate destructive action
        reset_button = gr.Button("Reset", variant="stop")
        
        # Primary action button to submit the request
        # variant="primary" gives it prominence and a green appearance
        go_button = gr.Button("Go!", variant="primary")
    
    # Set up the initial loading event that runs when the interface starts
    # This calls the setup() function to initialize the Sidekick instance
    # The empty lists indicate no inputs and that sidekick is the output
    ui.load(setup, [], [sidekick])
    
    # Connect the message input to the process_message function
    # This triggers when user presses Enter in the message field
    # The function receives sidekick, message, success_criteria, and chatbot as inputs
    # It returns updated chatbot and sidekick as outputs
    message.submit(process_message, [sidekick, message, success_criteria, chatbot], [chatbot, sidekick])
    
    # Connect the success criteria input to the same process_message function
    # This allows users to trigger processing by pressing Enter in either field
    # Provides flexibility in how users interact with the interface
    success_criteria.submit(process_message, [sidekick, message, success_criteria, chatbot], [chatbot, sidekick])
    
    # Connect the "Go!" button click event to the process_message function
    # This provides an explicit button for users who prefer clicking over pressing Enter
    # The same input/output pattern ensures consistent behavior across all triggers
    go_button.click(process_message, [sidekick, message, success_criteria, chatbot], [chatbot, sidekick])
    
    # Connect the reset button to the reset function
    # This clears all inputs and creates a fresh Sidekick instance
    # The empty input list and full output list handle the complete reset
    reset_button.click(reset, [], [message, success_criteria, chatbot, sidekick])

    
ui.launch(inbrowser=True)