import tensorflow as tf
from tensorflow.keras.models import load_model
import os

def freeze_graph(model, output_path):
    """
    Convert Keras model to frozen graph (.pb format)
    
    Args:
        model: Keras model instance
        output_path: Path where to save the .pb file
    """
    # Convert Keras model to ConcreteFunction
    full_model = tf.function(lambda x: model(x))
    concrete_function = full_model.get_concrete_function(
        tf.TensorSpec(model.inputs[0].shape, model.inputs[0].dtype)
    )

    # Get frozen ConcreteFunction
    from tensorflow.python.framework.convert_to_constants import convert_variables_to_constants_v2
    frozen_func = convert_variables_to_constants_v2(concrete_function)

    # Save the frozen graph
    tf.io.write_graph(
        graph_or_graph_def=frozen_func.graph,
        logdir=os.path.dirname(output_path),
        name=os.path.basename(output_path),
        as_text=False
    )

def export_model(model_path, output_path):
    """
    Load Keras model and export it to .pb format
    
    Args:
        model_path: Path to the saved Keras model (.h5 file)
        output_path: Path where to save the .pb file
    """
    try:
        # Load the Keras model
        model = load_model(model_path)
        
        # Create output directory if it doesn't exist
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        
        # Convert and save the model
        freeze_graph(model, output_path)
        print(f"Model successfully exported to: {output_path}")
        
    except Exception as e:
        print(f"Error exporting model: {str(e)}")

if __name__ == "__main__":
    # Example usage
    model_path = r"src\model\multi_layer_perceptron.keras"
    output_path = r"model\model.pb"
    export_model(model_path, output_path)
