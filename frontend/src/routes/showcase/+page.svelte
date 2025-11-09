<script>
  import CuttingBoard from './CuttingBoard.svelte'

  let cuttingBoard
</script>

<CuttingBoard bind:this={cuttingBoard} />

<br>

<button onclick={()=>{cuttingBoard.startAnimation()}}>
  #mybutton
</button>

<style>
  @import "./style.css";
</style>
