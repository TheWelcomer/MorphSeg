<script>
  import Bubbles from "./Bubbles.svelte"

  const Stage = {
    BEFORE: 0,
    WORDS: 1,
    CLEANUP: 2,
    MORPHEMES: 3,
  };

  let input = $state("What the Segma?");
  let stage = $state(Stage.BEFORE);
  let words = $state(splitWords(input));
  let morphemes = $state([["What"],["the"],["Seg","ma"]]);
  
  function splitWords(text) {
    return text.replace(/\s/g, " ")
               .split(" ")
               .filter((word)=>word.length > 0);
  }

  function segment(text) {
    return text.split(" ")
               .map((word)=>word.split(""))
               .filter((word)=>word.length > 0);
  }

  export function startAnimation(){
    words = splitWords(input);
    stage++;
  }
</script>

<div id=cutting-board>
  <img id=cutting-board-img src="/assets/Sprite-cuttingboard.png" />
  {#if stage == Stage.BEFORE}
    <div id=cutting-board-input bind:innerText={input} contenteditable=true />
  {:else if stage >= Stage.WORDS}
    <div id="word-container">
      {#if stage != Stage.MORPHEMES}
        {#each words as word, wIndex}
          <span class="word">
              <span class="word-inner word-style-{(wIndex % 5) + 1}">
                {word}
              </span>
          </span>&nbsp<span class="word-spacer" style="animation-delay: {wIndex * 0.25}s;" />
        {/each}
      {:else}
        {#each morphemes as word, wIndex}
          {#each word as morpheme, mIndex}
            <span class="word">
                <span class="word-inner word-style-{(wIndex % 5) + 1}">
                  {morpheme}
                </span>{#if mIndex != (word.length - 1)}
                  <span class="morpheme-spacer" />
                {/if}
            </span>
          {/each}&nbsp<span class="canon-word-spacer" />
        {/each}
      {/if}
    </div>
  {/if}
  {#if stage >= Stage.CLEANUP}
    <Bubbles />
  {/if}
</div>

<style>
  @import "./style.css";
  
  #cutting-board {
    align-items: center;
    justify-content: center;
    display: flex;
    position: relative;
  }

  #cutting-board-img {
    position: absolute;
    top: 0;
    left: 0;
    width: 100%;
    height: 100%;
    z-index: -5;
  }

  #word-container {
    width: 100%;
    margin: 2em;  
  }

  .word {
    display: inline-block;
    margin: 0.25em 0 0.25em 0;
  }

  .word-inner {
    padding: 0.1em;
    border-radius: 0.3em;
    border-style: solid;
    border-width: 0.15em;
  }

  .word-style-1 {
    background-color: #b82634;
    border-color: #961743;
  }

  .word-style-2 {
    background-color: #d3802e;
    border-color: #c16a38;
  }

  .word-style-3 {
    background-color: #d0a94e;
    border-color: #d78d43;
  }

  .word-style-4 {
    background-color: #489d3e;
    border-color: #407b51;
  }

  .word-style-5 {
    background-color: #8a4896;
    border-color: #663479;
  }

  .word-spacer {
    animation: 0.5s ease-out 1 both expand;
    animation-iteration-count: 1;
    display: inline-block;
  }

  .morpheme-spacer {
    animation: 0.5s ease-out 0.2s 1 both expand-less;
    animation-iteration-count: 1;
    display: inline-block;
  }

  .canon-word-spacer {
    display: inline-block;
    width: 1em;
  }


  @keyframes expand {
    from {
      width: 0em;
    }
    to {
      width: 1.0em;
    }
  }

  @keyframes expand-less {
    from {
      width: 0em;
    }
    to {
      width: 0.5em;
    }
  }
</style>
