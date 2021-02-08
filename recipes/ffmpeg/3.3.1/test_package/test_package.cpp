extern "C" {

#include <libavcodec/avcodec.h>
#include <libavfilter/avfilter.h>
#include <libavformat/avformat.h>

}

#include <iostream>
#include <set>
#include <string>
#include <vector>


template<class Container>
void print_all(const std::string& message, const Container& values) {
  if (values.empty()) {
    return;
  }
  std::cout << message << ":\n";
  for (const auto& value : values) {
    std::cout << "\t" << value << "\n";
  }
}

bool check(const std::vector<std::string>& to_check,
    const std::set<std::string>& available,
    const char* type,
    const char* subtype = nullptr) {
  std::vector<std::string> found;
  std::vector<std::string> not_found;

  for (const auto& name : to_check) {
    if (available.count(name)) {
      found.push_back(name);
    } else {
      not_found.push_back(name);
    }
  }

  std::cout << "checking " << type;
  if (subtype) {
    std::cout << "(" << subtype << ")";
  }
  std::cout << "...\n";
  print_all("Suppoted", found);
  print_all("Not supported", not_found);

  std::cout.flush();

  return not_found.empty();
}

std::set<std::string> get_input_formats_and_devices() {
  std::set<std::string> names;
  AVInputFormat* format = nullptr;
  while ((format = av_iformat_next(format))) {
    names.insert(format->name);
  }
  return names;
}

std::set<std::string> get_output_formats_and_devices() {
  std::set<std::string> names;
  AVOutputFormat* format = nullptr;
  while ((format = av_oformat_next(format))) {
    names.insert(format->name);
  }
  return names;
}

bool check_bitstream_filters(const std::vector<std::string>& filters_to_check) {
  std::set<std::string> available_filters;
  void* state = nullptr;
  const AVBitStreamFilter* filter = nullptr;
  while ((filter = av_bsf_next(&state))) {
    available_filters.insert(filter->name);
  }
  return check(filters_to_check, available_filters, "bitstream_filters");
}

bool check_filters(const std::vector<std::string>& filters_to_check) {
  std::set<std::string> available_filters;
  const AVFilter* filter = nullptr;
  while ((filter = avfilter_next(filter))) {
    available_filters.insert(filter->name);
  }
  return check(filters_to_check, available_filters, "filters");
}

bool check_input_formats(const std::vector<std::string>& formats_to_check,
    const std::set<std::string>& available_formats) {
  return check(formats_to_check, available_formats, "formats", "input");
}

bool check_output_formats(const std::vector<std::string>& formats_to_check,
    const std::set<std::string>& available_formats) {
  return check(formats_to_check, available_formats, "formats", "output");
}

bool check_input_devices(const std::vector<std::string>& devices_to_check,
    const std::set<std::string>& available_devices) {
  return check(devices_to_check, available_devices, "devices", "input");
}

bool check_output_devices(const std::vector<std::string>& devices_to_check,
    const std::set<std::string>& available_devices) {
  return check(devices_to_check, available_devices, "devices", "output");
}


bool check_encoders(const std::vector<std::string>& encoders_to_check) {
  std::set<std::string> available;
  for (const auto& name: encoders_to_check) {
    if (avcodec_find_encoder_by_name(name.c_str())) {
      available.insert(name);
    }
  }
  return check(encoders_to_check, available, "codecs", "encoders");
}

bool check_decoders(const std::vector<std::string>& decoders_to_check) {
  std::set<std::string> available;
  for (const auto& name: decoders_to_check) {
    if (avcodec_find_decoder_by_name(name.c_str())) {
      available.insert(name);
    }
  }
  return check(decoders_to_check, available, "codecs", "decoders");
}

const std::vector<std::string> input_and_output_formats = {
"aac",  // no output
"ac3",
"avi",
"flac",
"flv",
"h263",
"h264",
"hevc",
"hls",  // no input
"mjpeg",
"mp3",
"mpeg",
"mxg",  // no output
"ogg",
"rtp",
"rtsp"};

const std::vector<std::string> video_encoders = {
"dvvideo",
"mjpeg",
"mpeg1video",
"mpeg2video",
"mpeg4",
"flv",
"h261",
"h263",
"theora",
"vp8",
"msmpeg4v2",
"wmv1",
"wmv2"};

const std::vector<std::string> video_decoders = {
"dvvideo",
"mjpeg",
"mpeg1video",
"mpeg2video",
"mpeg4",
"mpeg4dd",
"mjpegdd",
"mpeg4di",
"mjpegdi",
"flv",
"h261",
"h263",
"h264",
"h265",
"hevc",
"theora",
"vp8",
"msmpeg4v1",
"msmpeg4v2",
"wmv1",
"wmv2"};


const std::vector<std::string> input_devices = {
"dv1394",
"jack",
"lavfi",
"libcdio",
"openal",
"oss",
#ifdef __linux__
"alsa",
"fbdev",
"pulse",
"video4linux2",
"v4l2",
"x11grab"
#endif
};


const std::vector<std::string> output_devices = {
"dv1394",
"opengl",
"oss",
"sdl",
#ifdef __linux__
"alsa",
"fbdev",
"pulse",
"v4l2",
"xv"
#endif
};

const std::vector<std::string> filters = {
"buffer",
"buffersink"
};

const std::vector<std::string> bitstream_filters = {
"h264_mp4toannexb",
"hevc_mp4toannexb"
};


int main() {
  avcodec_register_all();
  av_register_all();
  avfilter_register_all();

  const auto& available_input = get_input_formats_and_devices();
  const auto& available_output = get_output_formats_and_devices();

  const bool input_format_ok = check_input_formats(input_and_output_formats, available_input);
  const bool output_format_ok = check_output_formats(input_and_output_formats, available_output);

  const bool input_device_ok = check_input_devices(input_devices, available_input);
  const bool output_device_ok = check_output_devices(output_devices, available_output);

  const bool video_encoders_ok = check_encoders(video_encoders);
  const bool video_decoders_ok = check_decoders(video_decoders);

  const bool filters_ok = check_filters(filters);
  const bool bitstream_filters_ok = check_bitstream_filters(bitstream_filters);

  return 0;
}
